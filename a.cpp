#include <iostream>
#include <string_view>
#include <cstdlib>
#include <stdexcept>

namespace app {

class Greeter {
public:
    // Use string_view for efficient string passing
    explicit Greeter(std::string_view message) noexcept
        : m_message(message) {}

    // Mark member functions that don't modify state as const
    [[nodiscard]] auto getMessage() const noexcept -> std::string_view {
        return m_message;
    }

    // Use auto return type for better maintainability
    auto greet() const -> void {
        std::cout << getMessage() << '\n';
    }

private:
    std::string_view m_message;
};

// Use [[nodiscard]] to ensure return values are handled
[[nodiscard]] auto createGreeter(std::string_view message) -> Greeter {
    if (message.empty()) {
        throw std::invalid_argument("Message cannot be empty");
    }
    return Greeter{message};
}

} // namespace app

auto main() -> int {
    try {
        constexpr std::string_view message = "Hello, World!";
        auto greeter = app::createGreeter(message);
        greeter.greet();
        return EXIT_SUCCESS;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << '\n';
        return EXIT_FAILURE;
    }
}