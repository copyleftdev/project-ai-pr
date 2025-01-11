/**
 * @file secure_auth.c
 * @brief Secure authentication and input processing system
 * @version 1.0
 * 
 * This implementation provides secure user authentication, input validation,
 * and file handling with comprehensive error checking and logging.
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <openssl/sha.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/err.h>
#include <ctype.h>
#include <errno.h>
#include <syslog.h>

#define BUFFER_SIZE 50
#define DATA_SIZE 1024
#define INPUT_SIZE 20
#define SALT_SIZE 16
#define HASH_SIZE 32
#define MAX_USERNAME_LENGTH 32
#define MAX_PASSWORD_LENGTH 64
#define MAX_LINE_LENGTH 256
#define PASSWORD_DB_PATH "/etc/secure_passwd"

#ifdef DEBUG
    #define LOG_DEBUG(fmt, ...) fprintf(stderr, "DEBUG: " fmt "\n", ##__VA_ARGS__)
#else
    #define LOG_DEBUG(fmt, ...)
#endif

#define SECURE_FREE(ptr) do { if (ptr) { secure_free(ptr); ptr = NULL; } } while(0)
#define CHECK_NULL(ptr, msg) if (!ptr) { log_error(msg); return ERROR_NULL_POINTER; }

typedef enum {
    SUCCESS = 0,
    ERROR_NULL_POINTER = -1,
    ERROR_INVALID_INPUT = -2,
    ERROR_FILE_ACCESS = -3,
    ERROR_CRYPTO = -4,
    ERROR_BUFFER_OVERFLOW = -5,
    ERROR_AUTH_FAILED = -6
} ErrorCode;

typedef struct {
    unsigned char salt[SALT_SIZE];
    unsigned char hash[HASH_SIZE];
} HashData;

/**
 * @brief Securely wipes and frees memory
 * @param ptr Pointer to memory to be wiped
 * @param size Size of memory to wipe
 */
static void secure_free(void* ptr) {
    if (ptr) {
        OPENSSL_cleanse(ptr, sizeof(ptr));
        free(ptr);
    }
}

/**
 * @brief Logs error messages with error code
 * @param message Error message
 * @param code Error code
 */
static void log_error(const char* message) {
    syslog(LOG_ERR, "%s: %s", message, strerror(errno));
    LOG_DEBUG("Error: %s", message);
}

/**
 * @brief Initializes OpenSSL and system logging
 * @return ErrorCode indicating success or failure
 */
static ErrorCode initialize_system(void) {
    OpenSSL_add_all_algorithms();
    ERR_load_crypto_strings();
    openlog("secure_auth", LOG_PID | LOG_CONS, LOG_AUTH);
    return SUCCESS;
}

/**
 * @brief Cleans up OpenSSL and system logging
 */
static void cleanup_system(void) {
    EVP_cleanup();
    ERR_free_strings();
    closelog();
}

/**
 * @brief Processes input with secure bounds checking
 * @param input Input string to process
 * @return ErrorCode indicating success or failure
 */
ErrorCode process_input(const char* input) {
    CHECK_NULL(input, "Null input pointer");
    
    char buffer[BUFFER_SIZE] = {0};
    if (strlen(input) >= BUFFER_SIZE) {
        return ERROR_BUFFER_OVERFLOW;
    }
    
    if (strncpy(buffer, input, BUFFER_SIZE - 1) != buffer) {
        return ERROR_BUFFER_OVERFLOW;
    }
    
    LOG_DEBUG("Processing input: %s", buffer);
    return SUCCESS;
}

/**
 * @brief Computes secure hash using OpenSSL
 * @param password Password to hash
 * @param salt Salt value
 * @param hash Output hash buffer
 * @return ErrorCode indicating success or failure
 */
static ErrorCode compute_hash(const char* password, const unsigned char* salt, 
                            unsigned char* hash) {
    CHECK_NULL(password, "Null password pointer");
    CHECK_NULL(salt, "Null salt pointer");
    CHECK_NULL(hash, "Null hash pointer");

    ErrorCode result = ERROR_CRYPTO;
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    
    do {
        if (!ctx || 
            EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) != 1 ||
            EVP_DigestUpdate(ctx, salt, SALT_SIZE) != 1 ||
            EVP_DigestUpdate(ctx, password, strlen(password)) != 1) {
            break;
        }

        unsigned int hash_len;
        if (EVP_DigestFinal_ex(ctx, hash, &hash_len) != 1) {
            break;
        }

        result = SUCCESS;
    } while (0);

    if (ctx) {
        EVP_MD_CTX_free(ctx);
    }
    
    return result;
}

/**
 * @brief Validates and sanitizes username
 * @param input Input username
 * @param output Sanitized username buffer
 * @param output_size Size of output buffer
 * @return ErrorCode indicating success or failure
 */
static ErrorCode sanitize_username(const char* input, char* output, size_t output_size) {
    CHECK_NULL(input, "Null input username");
    CHECK_NULL(output, "Null output buffer");
    
    if (output_size < 1 || strlen(input) >= output_size) {
        return ERROR_BUFFER_OVERFLOW;
    }

    for (size_t i = 0; input[i] && i < output_size - 1; i++) {
        if (!isalnum(input[i]) && input[i] != '_' && input[i] != '-') {
            return ERROR_INVALID_INPUT;
        }
        output[i] = input[i];
    }
    
    return SUCCESS;
}

/**
 * @brief Validates user credentials
 * @param username Username to validate
 * @param password Password to validate
 * @return ErrorCode indicating success or failure
 */
ErrorCode validate_user(const char* username, const char* password) {
    CHECK_NULL(username, "Null username pointer");
    CHECK_NULL(password, "Null password pointer");
    
    if (strlen(username) >= MAX_USERNAME_LENGTH || 
        strlen(password) >= MAX_PASSWORD_LENGTH) {
        return ERROR_INVALID_INPUT;
    }

    char sanitized_username[MAX_USERNAME_LENGTH] = {0};
    ErrorCode result = sanitize_username(username, sanitized_username, 
                                       sizeof(sanitized_username));
    if (result != SUCCESS) {
        return result;
    }

    FILE* db = fopen(PASSWORD_DB_PATH, "r");
    if (!db) {
        log_error("Failed to open password database");
        return ERROR_FILE_ACCESS;
    }

    HashData stored_data = {0};
    char line[MAX_LINE_LENGTH];
    result = ERROR_AUTH_FAILED;

    while (fgets(line, sizeof(line), db)) {
        char stored_username[MAX_USERNAME_LENGTH] = {0};
        if (sscanf(line, "%31[^:]", stored_username) == 1 && 
            strcmp(stored_username, sanitized_username) == 0) {
            
            char* salt_pos = strchr(line, ':');
            if (!salt_pos || strlen(salt_pos) < 2*SALT_SIZE + 2*HASH_SIZE + 2) {
                continue;
            }

            salt_pos++;
            for (int i = 0; i < SALT_SIZE; i++) {
                if (sscanf(salt_pos + 2*i, "%2hhx", &stored_data.salt[i]) != 1) {
                    goto cleanup;
                }
            }

            salt_pos += 2*SALT_SIZE + 1;
            for (int i = 0; i < HASH_SIZE; i++) {
                if (sscanf(salt_pos + 2*i, "%2hhx", &stored_data.hash[i]) != 1) {
                    goto cleanup;
                }
            }

            unsigned char computed_hash[HASH_SIZE] = {0};
            if (compute_hash(password, stored_data.salt, computed_hash) == SUCCESS &&
                CRYPTO_memcmp(computed_hash, stored_data.hash, HASH_SIZE) == 0) {
                result = SUCCESS;
            }
            break;
        }
    }

cleanup:
    OPENSSL_cleanse(&stored_data, sizeof(stored_data));
    fclose(db);
    return result;
}

/**
 * @brief Handles file operations securely
 * @param filename Name of file to handle
 * @return ErrorCode indicating success or failure
 */
ErrorCode handle_file(const char* filename) {
    CHECK_NULL(filename, "Null filename pointer");
    
    FILE* fp = fopen(filename, "r");
    if (!fp) {
        log_error("Failed to open file");
        return ERROR_FILE_ACCESS;
    }

    char* data = calloc(DATA_SIZE, sizeof(char));
    if (!data) {
        fclose(fp);
        return ERROR_NULL_POINTER;
    }

    ErrorCode result = SUCCESS;
    size_t bytes_read = fread(data, 1, DATA_SIZE - 1, fp);
    
    if (ferror(fp)) {
        log_error("File read error");
        result = ERROR_FILE_ACCESS;
    }

    SECURE_FREE(data);
    fclose(fp);
    return result;
}

/**
 * @brief Main program entry point
 * @param argc Argument count
 * @param argv Argument vector
 * @return Program exit status
 */
int main(int argc, char* argv[]) {
    ErrorCode result = initialize_system();
    if (result != SUCCESS) {
        fprintf(stderr, "System initialization failed\n");
        return EXIT_FAILURE;
    }

    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input>\n", argv[0]);
        cleanup_system();
        return EXIT_FAILURE;
    }

    result = process_input(argv[1]);
    if (result != SUCCESS) {
        fprintf(stderr, "Error processing input\n");
        cleanup_system();
        return EXIT_FAILURE;
    }

    char temp[INPUT_SIZE] = {0};
    if (!fgets(temp, sizeof(temp), stdin)) {
        fprintf(stderr, "Error reading input\n");
        cleanup_system();
        return EXIT_FAILURE;
    }

    size_t len = strlen(temp);
    if (len > 0 && temp[len-1] == '\n') {
        temp[len-1] = '\0';
    }

    cleanup_system();
    return EXIT_SUCCESS;
}