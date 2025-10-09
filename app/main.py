# app/main.py

import socket
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any

from app.config import config
from app.routes.route_handlers import HandlerMixin
from app.utils.boot_check import perform_boot_check

def parse_query(path: str) -> Dict[str, Any]:
    """Parse query parameters from a URL path."""
    return parse_qs(urlparse(path).query)


class RequestHandler(BaseHTTPRequestHandler, HandlerMixin):
    """Main HTTP request handler delegating route logic to HandlerMixin."""

    def do_GET(self):
        parsed_path = urlparse(self.path)
        route = parsed_path.path
        query = parse_query(self.path)

        # 🪵 Debug logging
        print(f"\n[DEBUG] route: {route},\nquery: {json.dumps(query, indent=2)}")
        print(f"[DEBUG] parsed_path: {parsed_path}.\n")

        routes = {
            '/': self.handle_home,
            '/health': self.handle_health,
            '/yt_details': self.handle_yt_details,
            '/yt_thumbnail': self.handle_yt_thumbnail,
            '/yt_download': self.handle_yt_download,
        }

        handler = routes.get(route)
        if handler:
            try:
                handler(query)
            except Exception as e:
                self.write_json({
                    "status": "error",
                    "message": f"Internal server error: {str(e)}"
                }, 500)
        else:
            self.write_json({"error": "Not found"}, 404)


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def run_server():
    if is_port_in_use(config.port):
        print(f"⚠️ Port {config.port} already in use. Try changing it in your .env file.")
        return

    server_address = ('', config.port)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"Server running on port {config.port} in {config.env} mode")
    httpd.serve_forever()


if __name__ == '__main__':
    perform_boot_check()
    run_server()

