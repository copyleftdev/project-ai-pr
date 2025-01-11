#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <openssl/sha.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <ctype.h>

#define BUFFER_SIZE 50
#define DATA_SIZE 1024
#define INPUT_SIZE 20
#define SALT_SIZE 16
#define HASH_SIZE 32
#define MAX_USERNAME_LENGTH 32
#define MAX_PASSWORD_LENGTH 64

// Secure hash structure
typedef struct {
    unsigned char salt[SALT_SIZE];
    unsigned char hash[HASH_SIZE];
} HashData;

// Returns 0 on success, -1 on error
int process_input(const char* input) {
    if (!input) {
        return -1;
    }
    
    char buffer[BUFFER_SIZE];
    if (strncpy(buffer, input, BUFFER_SIZE - 1) != buffer) {
        return -1;
    }
    buffer[BUFFER_SIZE - 1] = '\0';
    
    printf("Processing: %s\n", buffer);
    return 0;
}

// Compute password hash with salt
static int compute_hash(const char* password, const unsigned char* salt, 
                       unsigned char* hash) {
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    if (!ctx) {
        return -1;
    }

    if (EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) != 1) {
        EVP_MD_CTX_free(ctx);
        return -1;
    }

    if (EVP_DigestUpdate(ctx, salt, SALT_SIZE) != 1) {
        EVP_MD_CTX_free(ctx);
        return -1;
    }

    if (EVP_DigestUpdate(ctx, password, strlen(password)) != 1) {
        EVP_MD_CTX_free(ctx);
        return -1;
    }

    unsigned int hash_len;
    if (EVP_DigestFinal_ex(ctx, hash, &hash_len) != 1) {
        EVP_MD_CTX_free(ctx);
        return -1;
    }

    EVP_MD_CTX_free(ctx);
    return 0;
}

// Sanitize username to prevent injection attacks
static int sanitize_username(const char* input, char* output, size_t output_size) {
    if (!input || !output || output_size < 1) {
        return -1;
    }

    size_t i;
    for (i = 0; i < output_size - 1 && input[i]; i++) {
        if (isalnum(input[i]) || input[i] == '_' || input[i] == '-') {
            output[i] = input[i];
        } else {
            return -1;  // Invalid character found
        }
    }
    output[i] = '\0';
    return 0;
}

// Returns 0 on success (valid user), -1 on error or invalid user
int validate_user(const char* username, const char* password) {
    if (!username || !password || 
        strlen(username) >= MAX_USERNAME_LENGTH || 
        strlen(password) >= MAX_PASSWORD_LENGTH) {
        return -1;
    }

    char sanitized_username[MAX_USERNAME_LENGTH];
    if (sanitize_username(username, sanitized_username, sizeof(sanitized_username)) != 0) {
        return -1;
    }

    // Open the password database file
    FILE* db = fopen("/etc/secure_passwd", "r");
    if (!db) {
        return -1;
    }

    char line[256];
    HashData stored_data;
    int found = 0;

    // Search for user and verify password
    while (fgets(line, sizeof(line), db)) {
        char stored_username[MAX_USERNAME_LENGTH];
        if (sscanf(line, "%31[^:]", stored_username) == 1) {
            if (strcmp(stored_username, sanitized_username) == 0) {
                // Parse salt and hash from the line
                char* salt_pos = strchr(line, ':');
                if (salt_pos && strlen(salt_pos) >= 2*SALT_SIZE + 2*HASH_SIZE + 2) {
                    salt_pos++;
                    for (int i = 0; i < SALT_SIZE; i++) {
                        sscanf(salt_pos + 2*i, "%2hhx", &stored_data.salt[i]);
                    }
                    salt_pos += 2*SALT_SIZE + 1;
                    for (int i = 0; i < HASH_SIZE; i++) {
                        sscanf(salt_pos + 2*i, "%2hhx", &stored_data.hash[i]);
                    }
                    found = 1;
                    break;
                }
            }
        }
    }
    fclose(db);

    if (!found) {
        return -1;
    }

    // Compute hash of provided password with stored salt
    unsigned char computed_hash[HASH_SIZE];
    if (compute_hash(password, stored_data.salt, computed_hash) != 0) {
        return -1;
    }

    // Compare computed hash with stored hash
    if (memcmp(computed_hash, stored_data.hash, HASH_SIZE) != 0) {
        return -1;
    }

    return 0;  // Valid user
}

int handle_file(const char* filename) {
    if (!filename) {
        return -1;
    }
    
    FILE* fp = NULL;
    char data[DATA_SIZE] = {0};
    
    fp = fopen(filename, "r");
    if (!fp) {
        return -1;
    }
    
    size_t bytes_read = fread(data, 1, DATA_SIZE - 1, fp);
    if (ferror(fp)) {
        fclose(fp);
        return -1;
    }
    
    data[bytes_read] = '\0';
    fclose(fp);
    return 0;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input>\n", argv[0]);
        return 1;
    }
    
    if (process_input(argv[1]) != 0) {
        fprintf(stderr, "Error processing input\n");
        return 1;
    }
    
    char temp[INPUT_SIZE] = {0};
    if (!fgets(temp, sizeof(temp), stdin)) {
        fprintf(stderr, "Error reading input\n");
        return 1;
    }
    
    size_t len = strlen(temp);
    if (len > 0 && temp[len-1] == '\n') {
        temp[len-1] = '\0';
    }
    
    return 0;
}