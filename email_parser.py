#!/usr/bin/env python3

import argparse
import concurrent.futures
import dataclasses
import datetime
import email.utils
import ipaddress
import json
import logging
import pathlib
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Pattern, Set, Tuple

@dataclass
class EmailLogEntry:
    timestamp: datetime.datetime
    message_id: str
    sender: str
    recipients: List[str]
    subject: Optional[str]
    status: str
    server_ip: Optional[ipaddress.IPv4Address] = None
    smtp_code: Optional[int] = None
    size: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id,
            'sender': self.sender,
            'recipients': self.recipients,
            'subject': self.subject,
            'status': self.status,
            'server_ip': str(self.server_ip) if self.server_ip else None,
            'smtp_code': self.smtp_code,
            'size': self.size
        }

class LogParser:
    """Advanced log parser with support for multiple log formats"""
    
    def __init__(self):
        self.patterns: Dict[str, Pattern] = {
            'postfix': re.compile(
                r'(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'
                r'.*?'
                r'(?P<message_id>[A-F0-9]{10,})'
                r'.*?'
                r'from=<(?P<sender>[^>]+)>'
                r'.*?'
                r'to=<(?P<recipients>[^>]+)>'
                r'.*?'
                r'status=(?P<status>\w+)'
            ),
            'exchange': re.compile(
                r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
                r'.*?'
                r'MessageId:\s*(?P<message_id>[^\s,]+)'
                r'.*?'
                r'Sender:\s*(?P<sender>[^\s,]+)'
                r'.*?'
                r'Recipients:\s*(?P<recipients>[^\s,]+)'
                r'.*?'
                r'Status:\s*(?P<status>[^\s,]+)'
            ),
            'sendmail': re.compile(
                r'(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'
                r'.*?'
                r't=(?P<message_id>[^,\s]+)'
                r'.*?'
                r'f=(?P<sender>[^,\s]+)'
                r'.*?'
                r'r=(?P<recipients>[^,\s]+)'
                r'.*?'
                r's=(?P<status>[^,\s]+)'
            )
        }
        self.timestamp_formats = {
            'postfix': '%b %d %H:%M:%S',
            'exchange': '%Y-%m-%d %H:%M:%S',
            'sendmail': '%b %d %H:%M:%S'
        }
        
    def parse_line(self, line: str, year: int = None) -> Optional[EmailLogEntry]:
        """Parse a single log line and return an EmailLogEntry if matched"""
        for format_name, pattern in self.patterns.items():
            match = pattern.search(line)
            if match:
                data = match.groupdict()
                
                # Parse timestamp
                ts_str = data['timestamp']
                ts_format = self.timestamp_formats[format_name]
                try:
                    if year:
                        ts_str = f"{ts_str} {year}"
                        ts_format = f"{ts_format} %Y"
                    timestamp = datetime.datetime.strptime(ts_str, ts_format)
                except ValueError:
                    logging.warning(f"Failed to parse timestamp: {ts_str}")
                    continue
                
                # Parse recipients
                recipients = [r.strip() for r in data['recipients'].split(',')]
                
                # Extract optional subject if present
                subject_match = re.search(r'subject=(?P<subject>[^,]+)', line)
                subject = subject_match.group('subject') if subject_match else None
                
                # Extract IP if present
                ip_match = re.search(r'ip=\[?(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]?', line)
                server_ip = ipaddress.ip_address(ip_match.group('ip')) if ip_match else None
                
                # Extract SMTP code if present
                smtp_match = re.search(r'smtp=(?P<smtp>\d{3})', line)
                smtp_code = int(smtp_match.group('smtp')) if smtp_match else None
                
                # Extract size if present
                size_match = re.search(r'size=(?P<size>\d+)', line)
                size = int(size_match.group('size')) if size_match else None
                
                return EmailLogEntry(
                    timestamp=timestamp,
                    message_id=data['message_id'],
                    sender=data['sender'],
                    recipients=recipients,
                    subject=subject,
                    status=data['status'],
                    server_ip=server_ip,
                    smtp_code=smtp_code,
                    size=size
                )
        return None

class EmailLogAnalyzer:
    """Advanced email log analyzer with statistics and filtering capabilities"""
    
    def __init__(self):
        self.parser = LogParser()
        self.entries: List[EmailLogEntry] = []
        self.sender_stats: Dict[str, int] = defaultdict(int)
        self.recipient_stats: Dict[str, int] = defaultdict(int)
        self.status_stats: Dict[str, int] = defaultdict(int)
        self.hourly_stats: Dict[int, int] = defaultdict(int)
        
    def process_file(self, file_path: pathlib.Path, year: int = None) -> None:
        """Process a log file and collect statistics"""
        with file_path.open('r') as f:
            for line in f:
                entry = self.parser.parse_line(line.strip(), year)
                if entry:
                    self.entries.append(entry)
                    self.update_stats(entry)
    
    def update_stats(self, entry: EmailLogEntry) -> None:
        """Update statistics for a single entry"""
        self.sender_stats[entry.sender] += 1
        for recipient in entry.recipients:
            self.recipient_stats[recipient] += 1
        self.status_stats[entry.status] += 1
        self.hourly_stats[entry.timestamp.hour] += 1
    
    def get_failed_deliveries(self) -> List[EmailLogEntry]:
        """Get all failed delivery attempts"""
        return [e for e in self.entries if e.status.lower() in {'bounced', 'failed', 'deferred'}]
    
    def get_top_senders(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get top email senders"""
        return sorted(self.sender_stats.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def get_top_recipients(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get top email recipients"""
        return sorted(self.recipient_stats.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def get_status_summary(self) -> Dict[str, int]:
        """Get summary of email delivery statuses"""
        return dict(self.status_stats)
    
    def get_hourly_distribution(self) -> Dict[int, int]:
        """Get hourly distribution of email traffic"""
        return dict(self.hourly_stats)
    
    def export_json(self, output_file: pathlib.Path) -> None:
        """Export analysis results to JSON"""
        data = {
            'entries': [e.to_dict() for e in self.entries],
            'stats': {
                'senders': dict(self.sender_stats),
                'recipients': dict(self.recipient_stats),
                'statuses': dict(self.status_stats),
                'hourly': dict(self.hourly_stats)
            }
        }
        with output_file.open('w') as f:
            json.dump(data, f, indent=2)

def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description='Advanced Email Log Analyzer')
    parser.add_argument('log_files', nargs='+', type=pathlib.Path,
                      help='Log files to analyze')
    parser.add_argument('--year', type=int,
                      help='Year for log entries (if not in timestamp)')
    parser.add_argument('--output', type=pathlib.Path,
                      help='Output JSON file for results')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose output')
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    analyzer = EmailLogAnalyzer()
    
    # Process log files
    for log_file in args.log_files:
        if not log_file.exists():
            logging.error(f"File not found: {log_file}")
            continue
        logging.info(f"Processing {log_file}")
        analyzer.process_file(log_file, args.year)
    
    # Print summary
    print("\nAnalysis Summary:")
    print("=" * 50)
    print(f"Total entries processed: {len(analyzer.entries)}")
    
    print("\nTop 5 Senders:")
    for sender, count in analyzer.get_top_senders(5):
        print(f"  {sender}: {count}")
    
    print("\nDelivery Status Summary:")
    for status, count in analyzer.get_status_summary().items():
        print(f"  {status}: {count}")
    
    print("\nHourly Distribution:")
    for hour, count in sorted(analyzer.get_hourly_distribution().items()):
        print(f"  {hour:02d}:00 - {count}")
    
    # Export results if requested
    if args.output:
        analyzer.export_json(args.output)
        print(f"\nResults exported to {args.output}")

if __name__ == '__main__':
    main()