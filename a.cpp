#include <iostream>
#include <string>
#include <vector>
#include <algorithm>

/**
 * Example "allowlist" of shell commands permitted by this program.
 * In real-world usage, you'd carefully design or omit this approach entirely
 * to avoid potential command injection.
 */
static const std::vector<std::string> ALLOWED_COMMANDS = {
    "ls",     // List directory
    "pwd",    // Print working directory
    "whoami", // Show current user
    // ... add other strictly required commands ...
};

/**
 * Checks if a given command is allowed. This is a trivial substring check;
 * real scenarios might require more robust validation (args, flags, etc.).
 */
bool is_command_allowed(const std::string& cmd) {
    // Simple approach: require the entire command to match an allowed entry
    return std::find(ALLOWED_COMMANDS.begin(), ALLOWED_COMMANDS.end(), cmd) 
           != ALLOWED_COMMANDS.end();
}

int main() {
    std::cout << "Enter a shell command to run (allowed commands: ls, pwd, whoami): ";
    
    // Safely read user input into a std::string (up to newline)
    std::string userInput;
    if (!std::getline(std::cin, userInput)) {
        std::cerr << "Error reading input or EOF reached.\n";
        return 1;
    }

    // Trim whitespace (optional convenience)
    if (!userInput.empty()) {
        // example: remove leading/trailing spaces (simple approach)
        const auto front = userInput.find_first_not_of(" \t\r\n");
        const auto back  = userInput.find_last_not_of(" \t\r\n");
        userInput = userInput.substr(front, back - front + 1);
    }

    // Check against allowed commands
    if (!is_command_allowed(userInput)) {
        std::cerr << "Error: That command is not allowed.\n";
        return 1;
    }

    // If allowed, safely run via std::system 
    // (Still not recommended for production, but safer than gets + system.)
    int result = std::system(userInput.c_str());
    if (result == -1) {
        std::cerr << "Failed to execute command.\n";
        return 1;
    }

    return 0;
}
