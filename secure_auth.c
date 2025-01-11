/**
 * @file secure_auth.c
 * @brief Implementation of secure authentication system
 */

#include "secure_auth.h"
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/err.h>
#include <openssl/crypto.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <syslog.h>
#include <sys/stat.h>
#include <unistd.h>

/* Version information */
#define AUTH_VERSION "2.0.0"
#define AUTH_MEMORY_CANARY 0xDEADBEEF

/* Internal structures */
typedef struct {
    char username[MAX_USERNAME_LENGTH];
    time_t last_attempt;
    unsigned int attempt_count;
    pthread_mutex_t lock;
} RateLimit;

typedef struct {
    unsigned char salt[SALT_SIZE];
    unsigned char hash[HASH_SIZE];
    uint32_t canary;
} HashData;

/* Global state */
static struct {
    int initialized;
    AuthConfig config;
    RateLimit* rate_limits;
    size_t rate_limit_count;
    pthread_mutex_t global_lock;
    pthread_mutex_t rate_limit_lock;
    void (*log_fn)(int, const char*);
} g_auth_state = {0};

/* Default configuration */
static const AuthConfig default_config = {
    .password_db_path = "/etc/secure_passwd",
    .max_login_attempts = MAX_LOGIN_ATTEMPTS,
    .login_timeout = LOGIN_TIMEOUT_SECONDS,
    .enable_security_checks = 1,
    .log_callback = NULL
};

/* Internal function declarations */
static void secure_log(int level, const char* format, ...);
static void* secure_malloc(size_t size);
static void secure_free(void* ptr);
static AuthErrorCode perform_security_checks(void);
static AuthErrorCode compute_hash(const char* password, const unsigned char* salt,
                                unsigned char* hash);
static AuthErrorCode validate_rate_limit(const char* username);
static AuthErrorCode read_password_file(const char* username, HashData* hash_data);

/* Logging implementation */
static void secure_log(int level, const char* format, ...) {
    char buffer[1024];
    va_list args;
    va_start(args, format);
    vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);

    if (g_auth_state.log_fn) {
        g_auth_state.log_fn(level, buffer);
    } else {
        syslog(level, "%s", buffer);
    }
}

/* Secure memory management */
static void* secure_malloc(size_t size) {
    if (size == 0 || size > DATA_SIZE) {
        return NULL;
    }

    size_t total_size = size + 2 * sizeof(uint32_t);
    void* ptr = malloc(total_size);
    if (!ptr) {
        return NULL;
    }

    uint32_t* canary_start = (uint32_t*)ptr;
    uint32_t* canary_end = (uint32_t*)((char*)ptr + total_size - sizeof(uint32_t));
    *canary_start = AUTH_MEMORY_CANARY;
    *canary_end = AUTH_MEMORY_CANARY;

    return (char*)ptr + sizeof(uint32_t);
}

static void secure_free(void* ptr) {
    if (!ptr) {
        return;
    }

    void* real_ptr = (char*)ptr - sizeof(uint32_t);
    uint32_t* canary_start = (uint32_t*)real_ptr;
    uint32_t* canary_end = (uint32_t*)((char*)ptr + 
                          *(size_t*)((char*)real_ptr + sizeof(size_t)));

    if (*canary_start != AUTH_MEMORY_CANARY || 
        *canary_end != AUTH_MEMORY_CANARY) {
        secure_log(LOG_CRIT, "Memory corruption detected!");
        abort();  // Critical security violation
    }

    OPENSSL_cleanse(real_ptr, *(size_t*)((char*)real_ptr + sizeof(size_t)));
    free(real_ptr);
}

/* Security checks */
static AuthErrorCode perform_security_checks(void) {
    if (!g_auth_state.config.enable_security_checks) {
        return AUTH_SUCCESS;
    }

    /* Check for debugger attachment */
    struct stat s;
    if (stat("/proc/self/status", &s) == 0) {
        FILE* f = fopen("/proc/self/status", "r");
        if (f) {
            char line[256];
            while (fgets(line, sizeof(line), f)) {
                if (strstr(line, "TracerPid:\t") && 
                    atoi(line + 10) != 0) {
                    fclose(f);
                    return AUTH_ERROR_SECURITY;
                }
            }
            fclose(f);
        }
    }

    /* Check privileges */
    if (geteuid() == 0) {
        secure_log(LOG_WARNING, "Running with root privileges");
    }

    return AUTH_SUCCESS;
}

/* Cryptographic operations */
static AuthErrorCode compute_hash(const char* password, const unsigned char* salt,
                                unsigned char* hash) {
    if (!password || !salt || !hash) {
        return AUTH_ERROR_NULL_POINTER;
    }

    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    if (!ctx) {
        return AUTH_ERROR_CRYPTO;
    }

    AuthErrorCode result = AUTH_ERROR_CRYPTO;
    
    do {
        if (EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) != 1) {
            break;
        }
        
        if (EVP_DigestUpdate(ctx, salt, SALT_SIZE) != 1) {
            break;
        }
        
        if (EVP_DigestUpdate(ctx, password, strlen(password)) != 1) {
            break;
        }

        unsigned int hash_len;
        if (EVP_DigestFinal_ex(ctx, hash, &hash_len) != 1) {
            break;
        }

        result = AUTH_SUCCESS;
    } while (0);

    EVP_MD_CTX_free(ctx);
    return result;
}

/* Rate limiting */
static AuthErrorCode validate_rate_limit(const char* username) {
    pthread_mutex_lock(&g_auth_state.rate_limit_lock);
    RateLimit* limit = NULL;

    /* Find existing rate limit entry */
    for (size_t i = 0; i < g_auth_state.rate_limit_count; i++) {
        if (strcmp(g_auth_state.rate_limits[i].username, username) == 0) {
            limit = &g_auth_state.rate_limits[i];
            break;
        }
    }

    /* Create new rate limit entry if needed */
    if (!limit && g_auth_state.rate_limit_count < 1000) {
        limit = &g_auth_state.rate_limits[g_auth_state.rate_limit_count++];
        strncpy(limit->username, username, MAX_USERNAME_LENGTH - 1);
        limit->username[MAX_USERNAME_LENGTH - 1] = '\0';
        limit->attempt_count = 0;
        pthread_mutex_init(&limit->lock, NULL);
    }

    AuthErrorCode result = AUTH_SUCCESS;

    if (limit) {
        pthread_mutex_lock(&limit->lock);
        time_t current_time = time(NULL);

        if (current_time - limit->last_attempt < g_auth_state.config.login_timeout &&
            limit->attempt_count >= g_auth_state.config.max_login_attempts) {
            result = AUTH_ERROR_RATE_LIMIT;
        } else {
            limit->attempt_count++;
            limit->last_attempt = current_time;
        }

        pthread_mutex_unlock(&limit->lock);
    }

    pthread_mutex_unlock(&g_auth_state.rate_limit_lock);
    return result;
}

/* Password file operations */
static AuthErrorCode read_password_file(const char* username, HashData* hash_data) {
    FILE* db = fopen(g_auth_state.config.password_db_path, "r");
    if (!db) {
        return AUTH_ERROR_FILE_ACCESS;
    }

    AuthErrorCode result = AUTH_ERROR_AUTH_FAILED;
    char line[256];

    while (fgets(line, sizeof(line), db)) {
        char stored_username[MAX_USERNAME_LENGTH];
        if (sscanf(line, "%31[^:]", stored_username) == 1 &&
            strcmp(stored_username, username) == 0) {
            
            char* salt_pos = strchr(line, ':');
            if (!salt_pos || strlen(salt_pos) < 2*SALT_SIZE + 2*HASH_SIZE + 2) {
                break;
            }

            salt_pos++;
            for (int i = 0; i < SALT_SIZE; i++) {
                if (sscanf(salt_pos + 2*i, "%2hhx", &hash_data->salt[i]) != 1) {
                    goto cleanup;
                }
            }

            salt_pos += 2*SALT_SIZE + 1;
            for (int i = 0; i < HASH_SIZE; i++) {
                if (sscanf(salt_pos + 2*i, "%2hhx", &hash_data->hash[i]) != 1) {
                    goto cleanup;
                }
            }

            result = AUTH_SUCCESS;
            break;
        }
    }

cleanup:
    fclose(db);
    return result;
}

/* Public API implementation */
AuthErrorCode auth_initialize(const AuthConfig* config) {
    if (g_auth_state.initialized) {
        return AUTH_ERROR_INITIALIZATION;
    }

    /* Initialize OpenSSL */
    OpenSSL_add_all_algorithms();
    ERR_load_crypto_strings();

    /* Initialize logging */
    openlog("secure_auth", LOG_PID | LOG_CONS, LOG_AUTH);

    /* Set configuration */
    if (config) {
        memcpy(&g_auth_state.config, config, sizeof(AuthConfig));
    } else {
        memcpy(&g_auth_state.config, &default_config, sizeof(AuthConfig));
    }

    /* Initialize mutexes */
    pthread_mutex_init(&g_auth_state.global_lock, NULL);
    pthread_mutex_init(&g_auth_state.rate_limit_lock, NULL);

    /* Allocate rate limiting structure */
    g_auth_state.rate_limits = secure_malloc(sizeof(RateLimit) * 1000);
    if (!g_auth_state.rate_limits) {
        return AUTH_ERROR_MEMORY;
    }

    g_auth_state.initialized = 1;
    return AUTH_SUCCESS;
}

void auth_cleanup(void) {
    if (!g_auth_state.initialized) {
        return;
    }

    /* Clean up rate limiting */
    if (g_auth_state.rate_limits) {
        for (size_t i = 0; i < g_auth_state.rate_limit_count; i++) {
            pthread_mutex_destroy(&g_auth_state.rate_limits[i].lock);
        }
        secure_free(g_auth_state.rate_limits);
    }

    /* Clean up mutexes */
    pthread_mutex_destroy(&g_auth_state.global_lock);
    pthread_mutex_destroy(&g_auth_state.rate_limit_lock);

    /* Clean up OpenSSL */
    EVP_cleanup();
    ERR_free_strings();
    closelog();

    memset(&g_auth_state, 0, sizeof(g_auth_state));
}

AuthErrorCode auth_process_input(const char* input, size_t max_length) {
    if (!g_auth_state.initialized) {
        return AUTH_ERROR_INITIALIZATION;
    }

    if (!input) {
        return AUTH_ERROR_NULL_POINTER;
    }

    if (strlen(input) >= max_length) {
        return AUTH_ERROR_BUFFER_OVERFLOW;
    }

    char* sanitized = secure_malloc(max_length);
    if (!sanitized) {
        return AUTH_ERROR_MEMORY;
    }

    AuthErrorCode result = AUTH_SUCCESS;
    if (strncpy(sanitized, input, max_length - 1) != sanitized) {
        result = AUTH_ERROR_BUFFER_OVERFLOW;
    }

    secure_free(sanitized);
    return result;
}

AuthErrorCode auth_validate_user(const char* username, const char* password) {
    if (!g_auth_state.initialized) {
        return AUTH_ERROR_INITIALIZATION;
    }

    if (!username || !password) {
        return AUTH_ERROR_NULL_POINTER;
    }

    if (strlen(username) >= MAX_USERNAME_LENGTH || 
        strlen(password) >= MAX_PASSWORD_LENGTH) {
        return AUTH_ERROR_INVALID_INPUT;
    }

    /* Check rate limiting */
    AuthErrorCode result = validate_rate_limit(username);
    if (result != AUTH_SUCCESS) {
        return result;
    }

    /* Read stored password data */
    HashData stored_data = {0};
    result = read_password_file(username, &stored_data);
    if (result != AUTH_SUCCESS) {
        return result;
    }

    /* Compute and verify hash */
    unsigned char computed_hash[HASH_SIZE];
    result = compute_hash(password, stored_data.salt, computed_hash);
    if (result != AUTH_SUCCESS) {
        return result;
    }

    /* Constant-time comparison */
    if (CRYPTO_memcmp(computed_hash, stored_data.hash, HASH_SIZE) != 0) {
        return AUTH_ERROR_AUTH_FAILED;
    }

    return AUTH_SUCCESS;
}

AuthErrorCode auth_handle_file(const char* filename) {
    if (!g_auth_state.initialized) {
        return AUTH_ERROR_INITIALIZATION;
    }

    if (!filename) {
        return AUTH_ERROR_NULL_POINTER;
    }

    FILE* fp = fopen(filename, "r");
    if (!fp) {
        return AUTH_ERROR_FILE_ACCESS;
    }

    char* data = secure_malloc(DATA_SIZE);
    if (!data) {
        fclose(fp);
        return AUTH_ERROR_MEMORY;
    }

    AuthErrorCode result = AUTH_SUCCESS;
    size_t bytes_read = fread(data, 1, DATA_SIZE - 1, fp);
    
    if (ferror(fp)) {
        result = AUTH_ERROR_FILE_ACCESS;
    }

    secure_free(data);
    fclose(fp);
    return result;
}

const char* auth_error_string(AuthErrorCode error_code) {
    switch (error_code) {
        case AUTH_SUCCESS:
            return "Success";
        case AUTH_ERROR_NULL_POINTER:
            return "Null pointer error";
        case AUTH_ERROR_INVALID_INPUT:
            return "Invalid input";
        case AUTH_ERROR_FILE_ACCESS:
            return "File access error";
        case AUTH_ERROR_CRYPTO:
            return "Cryptographic operation failed";
        case AUTH_ERROR_BUFFER_OVERFLOW:
            return "Buffer overflow detected";
        case AUTH_ERROR_AUTH_FAILED:
            return "Authentication failed";
        case AUTH_ERROR_RATE_LIMIT:
            return "Rate limit exceeded";
        case AUTH_ERROR_SYSTEM:
            return "System error";
        case AUTH_ERROR_MEMORY:
            return "Memory allocation error";
        case AUTH_ERROR_PERMISSION:
            return "Permission denied";
        case AUTH_ERROR_SECURITY:
            return "Security check failed";
        case AUTH_ERROR_INITIALIZATION:
            return "System not initialized";
        default:
            return "Unknown error";
    }
}

const char* auth_get_version(void) {
    return AUTH_VERSION;
}