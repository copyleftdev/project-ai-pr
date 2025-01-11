/**
 * @file secure_auth.h
 * @brief Enterprise-grade secure authentication system
 * @version 2.0
 *
 * This header provides a comprehensive API for secure user authentication,
 * input validation, and file handling. The implementation follows security
 * best practices including:
 * - FIPS 140-2 compliant cryptographic operations
 * - Protection against buffer overflows
 * - Memory corruption detection
 * - Timing attack mitigation
 * - Rate limiting and brute force protection
 *
 * @note Thread-safe implementation required for all functions
 * @warning This system requires secure storage for password database
 */

#ifndef SECURE_AUTH_H
#define SECURE_AUTH_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Configuration constants for the authentication system
 * @note These values can be overridden at compile time
 */
#ifndef BUFFER_SIZE
#define BUFFER_SIZE 50
#endif

#ifndef DATA_SIZE
#define DATA_SIZE 1024
#endif

#ifndef SALT_SIZE
#define SALT_SIZE 32  /* NIST recommended minimum for hash salt */
#endif

#ifndef HASH_SIZE
#define HASH_SIZE 32  /* SHA-256 output size */
#endif

#ifndef MAX_USERNAME_LENGTH
#define MAX_USERNAME_LENGTH 32
#endif

#ifndef MAX_PASSWORD_LENGTH
#define MAX_PASSWORD_LENGTH 64
#endif

#ifndef MAX_LOGIN_ATTEMPTS
#define MAX_LOGIN_ATTEMPTS 5
#endif

#ifndef LOGIN_TIMEOUT_SECONDS
#define LOGIN_TIMEOUT_SECONDS 300  /* 5 minutes */
#endif

/**
 * @brief Error codes returned by the authentication system
 */
typedef enum {
    AUTH_SUCCESS = 0,
    AUTH_ERROR_NULL_POINTER = -1,
    AUTH_ERROR_INVALID_INPUT = -2,
    AUTH_ERROR_FILE_ACCESS = -3,
    AUTH_ERROR_CRYPTO = -4,
    AUTH_ERROR_BUFFER_OVERFLOW = -5,
    AUTH_ERROR_AUTH_FAILED = -6,
    AUTH_ERROR_RATE_LIMIT = -7,
    AUTH_ERROR_SYSTEM = -8,
    AUTH_ERROR_MEMORY = -9,
    AUTH_ERROR_PERMISSION = -10,
    AUTH_ERROR_SECURITY = -11,
    AUTH_ERROR_INITIALIZATION = -12
} AuthErrorCode;

/**
 * @brief Authentication configuration structure
 */
typedef struct {
    const char* password_db_path;     /* Path to password database */
    unsigned int max_login_attempts;   /* Maximum failed login attempts */
    unsigned int login_timeout;        /* Timeout period in seconds */
    int enable_security_checks;        /* Runtime security checks flag */
    void (*log_callback)(int level, const char* message);  /* Custom logging callback */
} AuthConfig;

/**
 * @brief Initialize the authentication system
 * 
 * Must be called before any other functions. Sets up cryptographic subsystem,
 * initializes logging, and performs security checks.
 *
 * @param config Pointer to configuration structure (NULL for defaults)
 * @return AuthErrorCode indicating success or failure
 */
AuthErrorCode auth_initialize(const AuthConfig* config);

/**
 * @brief Clean up and free resources used by the authentication system
 * 
 * Should be called when the authentication system is no longer needed.
 * Ensures secure cleanup of sensitive data.
 */
void auth_cleanup(void);

/**
 * @brief Process and validate input string
 *
 * Performs bounds checking and sanitization of input data.
 * 
 * @param input Input string to process
 * @param max_length Maximum allowed length
 * @return AuthErrorCode indicating success or failure
 */
AuthErrorCode auth_process_input(const char* input, size_t max_length);

/**
 * @brief Validate user credentials
 *
 * Performs secure user authentication with rate limiting and brute force protection.
 * 
 * @param username Username to validate
 * @param password Password to verify
 * @return AuthErrorCode indicating success or failure
 */
AuthErrorCode auth_validate_user(const char* username, const char* password);

/**
 * @brief Securely handle file operations
 *
 * Provides secure file handling with proper error checking and resource management.
 * 
 * @param filename Name of file to handle
 * @return AuthErrorCode indicating success or failure
 */
AuthErrorCode auth_handle_file(const char* filename);

/**
 * @brief Get string representation of error code
 *
 * Converts an AuthErrorCode to a human-readable string.
 * 
 * @param error_code Error code to convert
 * @return Constant string describing the error
 */
const char* auth_error_string(AuthErrorCode error_code);

/**
 * @brief Get current version of the authentication system
 *
 * @return Version string in format "MAJOR.MINOR.PATCH"
 */
const char* auth_get_version(void);

#ifdef __cplusplus
}
#endif

#endif /* SECURE_AUTH_H */