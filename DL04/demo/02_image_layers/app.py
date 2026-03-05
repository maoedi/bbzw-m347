import os
from http.server import BaseHTTPRequestHandler, HTTPServer


def get_who() -> str:
    return os.environ.get("WHO", "World")


def get_port() -> int:
    return int(os.environ.get("PORT", "8080"))


class HelloHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found\n")
            return

        message = f"Hallo {get_who()}. Ich wünsche, du wärst hier.\n"

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        # Logs im Unterricht ruhig halten
        return


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", get_port()), HelloHandler)
    server.serve_forever()