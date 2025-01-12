#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <sstream>

/**
 * Example "allowlist" of shell commands permitted by this program.
 * In real-world usage, you'd carefully design or omit this approach
 * to avoid potential command injection altogether.
 */
static const std::vector<std::string> ALLOWED_COMMANDS = {
    "ls",      // List directory
    "pwd",     // Print working directory
    "whoami",  // Show current user
    // Add others only if absolutely necessary
};

/**
 * Splits a string into tokens, e.g. "ls -l /home" -> ["ls", "-l", "/home"].
 * Helps us separate the base command from its arguments.
 */
std::vector<std::string> tokenize(const std::string &input) {
    std::vector<std::string> tokens;
    std::istringstream iss(input);
    std::string token;
    while (iss >> token) {
        tokens.push_back(token);
    }
    return tokens;
}

/**
 * Checks if a given command (the first token) is in the ALLOWED_COMMANDS.
 */
bool is_base_command_allowed(const std::string &cmd) {
    return std::find(ALLOWED_COMMANDS.begin(), ALLOWED_COMMANDS.end(), cmd)
           != ALLOWED_COMMANDS.end();
}

int main() {
    std::cout << "Enter a shell command to run (allowed: ls, pwd, whoami): ";

    // Safely read user input into a std::string
    std::string userInput;
    if (!std::getline(std::cin, userInput)) {
        std::cerr << "Error reading input or EOF reached.\n";
        return 1;
    }

    // Tokenize the input: first token is the base command; subsequent tokens are arguments
    std::vector<std::string> tokens = tokenize(userInput);
    if (tokens.empty()) {
        std::cerr << "No command entered.\n";
        return 1;
    }

    // The first token (base command) must match our allowlist
    const std::string &baseCmd = tokens[0];
    if (!is_base_command_allowed(baseCmd)) {
        std::cerr << "[SECURITY] Denied: Command \"" << baseCmd << "\" is not in the allowed list.\n";
        return 1;
    }

    // Optional: further checks on arguments if you want to allow only certain flags, etc.
    // For example:
    //   for (size_t i = 1; i < tokens.size(); i++) {
    //       // Validate each token carefully
    //   }

    // Construct a sanitized command string for system()
    // Minimal version: rejoin tokens with spaces
    std::ostringstream oss;
    for (size_t i = 0; i < tokens.size(); ++i) {
        if (i > 0) {
            oss << " ";  // separate tokens by space
        }
        oss << tokens[i];
    }
    std::string safeCommand = oss.str();

    // For demonstration purposes, using system() is still risky.
    // A truly secure design might replicate or wrap the needed functionality without calling the shell.
    int result = std::system(safeCommand.c_str());
    if (result == -1) {
        std::cerr << "[ERROR] Failed to execute command.\n";
        return 1;
    }

    std::cout << "[INFO] Command completed with exit code: " << WEXITSTATUS(result) << "\n";
    return 0;
}
