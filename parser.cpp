#include <string>
#include <string_view>
#include <unordered_map>
#include <optional>
#include <stdexcept>
#include <algorithm>
#include <memory>


// This code defines an HTTP request parser that can parse raw HTTP request strings
// into structured HttpRequest objects. It includes error handling for invalid
// request formats and supports parsing of request lines, headers, and bodies.
class HttpParserError : public std::runtime_error {
    using std::runtime_error::runtime_error;
};

class HttpRequest final {
public:
    using Headers = std::unordered_map<std::string, std::string, std::hash<std::string>, std::equal_to<>>;
    
private:
    std::string method_;
    std::string path_;
    std::string version_;
    Headers headers_;
    std::string body_;

public:
    // Use string_view for efficient read-only access
    [[nodiscard]] std::string_view method() const noexcept { return method_; }
    [[nodiscard]] std::string_view path() const noexcept { return path_; }
    [[nodiscard]] std::string_view version() const noexcept { return version_; }
    [[nodiscard]] const Headers& headers() const noexcept { return headers_; }
    [[nodiscard]] std::string_view body() const noexcept { return body_; }

    // Friend declaration for the parser
    friend class HttpParser;
};

class HttpParser final {
public:
    // Use string_view for efficient parsing without copying
    [[nodiscard]] std::optional<HttpRequest> parse(std::string_view raw_request) const {
        try {
            return parse_impl(raw_request);
        } catch (const std::exception&) {
            return std::nullopt;
        }
    }

private:
    [[nodiscard]] HttpRequest parse_impl(std::string_view raw_request) const {
        HttpRequest request;
        size_t pos = 0;
        size_t end_pos;

        // Parse request line
        if ((end_pos = raw_request.find("\r\n", pos)) == std::string_view::npos) {
            throw HttpParserError("Invalid request line");
        }
        parse_request_line(raw_request.substr(pos, end_pos - pos), request);
        pos = end_pos + 2;

        // Parse headers
        while (pos < raw_request.size()) {
            end_pos = raw_request.find("\r\n", pos);
            if (end_pos == std::string_view::npos) {
                throw HttpParserError("Invalid header format");
            }

            // Check for end of headers
            if (pos == end_pos) {
                pos += 2;
                break;
            }

            parse_header(raw_request.substr(pos, end_pos - pos), request);
            pos = end_pos + 2;
        }

        // Parse body
        if (pos < raw_request.size()) {
            request.body_ = std::string(raw_request.substr(pos));
        }

        return request;
    }

    static void parse_request_line(std::string_view line, HttpRequest& request) {
        size_t method_end = line.find(' ');
        if (method_end == std::string_view::npos) {
            throw HttpParserError("Invalid request line format");
        }

        size_t path_end = line.find(' ', method_end + 1);
        if (path_end == std::string_view::npos) {
            throw HttpParserError("Invalid request line format");
        }

        request.method_ = std::string(line.substr(0, method_end));
        request.path_ = std::string(line.substr(method_end + 1, path_end - method_end - 1));
        request.version_ = std::string(line.substr(path_end + 1));
        
        // Validate HTTP method
        if (!is_valid_method(request.method_)) {
            throw HttpParserError("Invalid HTTP method");
        }
    }

    static void parse_header(std::string_view line, HttpRequest& request) {
        size_t colon_pos = line.find(':');
        if (colon_pos == std::string_view::npos) {
            throw HttpParserError("Invalid header format");
        }

        std::string_view key = line.substr(0, colon_pos);
        std::string_view value = line.substr(colon_pos + 1);

        // Trim whitespace
        value = trim(value);
        
        if (!key.empty() && !value.empty()) {
            request.headers_.emplace(
                std::string(key),
                std::string(value)
            );
        }
    }

    [[nodiscard]] static std::string_view trim(std::string_view str) noexcept {
        const auto first = str.find_first_not_of(" \t\r\n");
        if (first == std::string_view::npos) return {};
        
        const auto last = str.find_last_not_of(" \t\r\n");
        return str.substr(first, last - first + 1);
    }

    [[nodiscard]] static bool is_valid_method(const std::string& method) noexcept {
        static const auto valid_methods = std::array{
            "GET", "POST", "PUT", "DELETE", "HEAD", 
            "OPTIONS", "PATCH", "TRACE", "CONNECT"
        };
        
        return std::find(valid_methods.begin(), valid_methods.end(), method) 
               != valid_methods.end();
    }
};