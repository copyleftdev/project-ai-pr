package main

import (
	"context"
	"crypto/tls"
	"errors"
	"flag"
	"fmt"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

// Config holds the application configuration
type Config struct {
	target  string
	timeout time.Duration
	verbose bool
}

// TLSChecker handles TLS connection analysis
type TLSChecker struct {
	config     Config
	mu         sync.RWMutex
	results    map[uint16]bool
	errCount   int
	tlsVersion uint16
}

// NewTLSChecker creates a new instance of TLSChecker
func NewTLSChecker(cfg Config) *TLSChecker {
	return &TLSChecker{
		config:  cfg,
		results: make(map[uint16]bool),
	}
}

// Run executes the TLS checking process
func (tc *TLSChecker) Run(ctx context.Context) error {
	// Initial connection to get TLS version
	if err := tc.checkTLSVersion(ctx); err != nil {
		return fmt.Errorf("initial TLS check failed: %w", err)
	}

	// Test cipher suites concurrently
	return tc.testCipherSuites(ctx)
}

func (tc *TLSChecker) checkTLSVersion(ctx context.Context) error {
	conn, err := tc.connect(ctx, &tls.Config{
		InsecureSkipVerify: true,
	})
	if err != nil {
		return err
	}
	defer conn.Close()

	tc.tlsVersion = conn.ConnectionState().Version
	return nil
}

func (tc *TLSChecker) connect(ctx context.Context, cfg *tls.Config) (*tls.Conn, error) {
	dialer := &net.Dialer{
		Timeout:   tc.config.timeout,
		KeepAlive: tc.config.timeout,
	}

	conn, err := tls.DialWithDialer(dialer, "tcp", tc.config.target, cfg)
	if err != nil {
		var netErr net.Error
		if errors.As(err, &netErr) && netErr.Timeout() {
			return nil, fmt.Errorf("connection timeout: %w", err)
		}
		return nil, fmt.Errorf("connection failed: %w", err)
	}

	return conn, nil
}

func (tc *TLSChecker) testCipherSuites(ctx context.Context) error {
	var wg sync.WaitGroup
	semaphore := make(chan struct{}, 10) // Limit concurrent connections

	for _, suite := range tls.CipherSuites() {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case semaphore <- struct{}{}:
		}

		wg.Add(1)
		go func(suite *tls.CipherSuite) {
			defer wg.Done()
			defer func() { <-semaphore }()

			cfg := &tls.Config{
				InsecureSkipVerify: true,
				CipherSuites:       []uint16{suite.ID},
				MinVersion:         tc.tlsVersion,
				MaxVersion:         tc.tlsVersion,
			}

			conn, err := tc.connect(ctx, cfg)
			if err != nil {
				if tc.config.verbose {
					fmt.Printf("Failed testing %s: %v\n", suite.Name, err)
				}
				tc.recordResult(suite.ID, false)
				return
			}
			defer conn.Close()

			tc.recordResult(suite.ID, true)
		}(suite)
	}

	wg.Wait()
	return nil
}

func (tc *TLSChecker) recordResult(suiteID uint16, supported bool) {
	tc.mu.Lock()
	defer tc.mu.Unlock()
	tc.results[suiteID] = supported
	if !supported {
		tc.errCount++
	}
}

func (tc *TLSChecker) printResults() {
	fmt.Printf("\nTLS Connection Information for %s:\n", tc.config.target)
	fmt.Printf("TLS Version: %s\n\n", getTLSVersionString(tc.tlsVersion))

	fmt.Println("Supported Cipher Suites:")
	for _, suite := range tls.CipherSuites() {
		supported := tc.results[suite.ID]
		if supported {
			fmt.Printf("✓ %s\n", suite.Name)
		} else if tc.config.verbose {
			fmt.Printf("✗ %s\n", suite.Name)
		}
	}

	fmt.Printf("\nSummary: %d supported, %d unsupported cipher suites\n",
		len(tc.results)-tc.errCount, tc.errCount)
}

func getTLSVersionString(version uint16) string {
	versions := map[uint16]string{
		tls.VersionTLS10: "TLS 1.0",
		tls.VersionTLS11: "TLS 1.1",
		tls.VersionTLS12: "TLS 1.2",
		tls.VersionTLS13: "TLS 1.3",
	}
	if v, ok := versions[version]; ok {
		return v
	}
	return fmt.Sprintf("Unknown (0x%04x)", version)
}

func main() {
	cfg := Config{}
	flag.StringVar(&cfg.target, "url", "", "Target URL (e.g., example.com:443)")
	flag.DurationVar(&cfg.timeout, "timeout", 5*time.Second, "Connection timeout")
	flag.BoolVar(&cfg.verbose, "verbose", false, "Show detailed output including failures")
	flag.Parse()

	if cfg.target == "" {
		flag.Usage()
		os.Exit(1)
	}

	// Create context with cancellation
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle OS signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigChan
		cancel()
	}()

	checker := NewTLSChecker(cfg)
	if err := checker.Run(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	checker.printResults()
}
