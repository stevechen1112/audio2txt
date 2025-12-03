"""
Simple HTTP server that always returns index.html for root requests.
"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class FrontendHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()


if __name__ == "__main__":
    root = Path(__file__).parent
    server_address = ("0.0.0.0", 5173)
    handler = FrontendHandler
    handler.directory = str(root)
    httpd = ThreadingHTTPServer(server_address, handler)
    print(f"Serving minimal_frontend on http://{server_address[0]}:{server_address[1]}")
    httpd.serve_forever()
