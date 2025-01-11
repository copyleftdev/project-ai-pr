#include <string>
#include <unordered_map>
#include <sstream>
#include <vector>

struct HttpRequest {
    std::string method;
    std::string path;
    std::string version;
    std::unordered_map<std::string, std::string> headers;
    std::string body;
};

class HttpParser {
public:
    HttpRequest parse(const std::string& raw_request) {
        HttpRequest request;
        std::istringstream stream(raw_request);
        std::string line;

        if (std::getline(stream, line)) {
            parseRequestLine(line, request);
        }

        while (std::getline(stream, line) && line != "\r") {
            if (line.empty()) break;
            parseHeader(line, request);
        }

        std::string body;
        while (std::getline(stream, line)) {
            body += line + "\n";
        }
        request.body = body;

        return request;
    }

private:
    void parseRequestLine(const std::string& line, HttpRequest& request) {
        std::istringstream lineStream(line);
        lineStream >> request.method >> request.path >> request.version;
    }

    void parseHeader(const std::string& line, HttpRequest& request) {
        size_t colonPos = line.find(':');
        if (colonPos == std::string::npos) return;

        std::string key = line.substr(0, colonPos);
        std::string value = line.substr(colonPos + 1);
        value.erase(0, value.find_first_not_of(" "));
        value.erase(value.find_last_not_of("\r") + 1);

        request.headers[key] = value;
    }
};