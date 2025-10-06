import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from app.config import config
from app.routes.basic_routes import home, health
from app.routes.yt_details import yt_details
import socket
from app.utils.boot_check import perform_boot_check
from app.routes.yt_thumbnail import get_thumbnail_url

class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path == '/':
            self._set_headers()
            self.wfile.write(json.dumps(home()).encode())
        elif self.path == '/health':
            self._set_headers()
            self.wfile.write(json.dumps(health()).encode())
        elif self.path.startswith('/yt_details'):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            url = query.get('url', [None])[0]
            if not url:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'url' parameter"}).encode())
            else:
                self._set_headers()
                self.wfile.write(json.dumps(yt_details(url)).encode())
        elif self.path.startswith('/yt_thumbnail'):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            url = query.get('url', [None])[0]
            download_flag = query.get('download', ['false'])[0].lower() == 'true'

            if not url:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "Missing 'url' query parameter."
                }).encode())
            else:
                result = get_thumbnail_url(url, download=download_flag)

                # If actual image requested and successful
                if download_flag and result.get("status") == "success" and "image_bytes" in result:
                    self.send_response(200)
                    self.send_header('Content-Type', result.get("content_type", "image/jpeg"))
                    self.end_headers()
                    self.wfile.write(result["image_bytes"])
                else:
                    code = 200 if result.get("status") == "success" else 400
                    self._set_headers(code)
                    self.wfile.write(json.dumps(result).encode())
        elif self.path.startswith('/yt_download'):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            url = query.get('url', [None])[0]

            if not url:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "Missing 'url' query parameter."
                }).encode())
            else:
                from app.routes.yt_download import yt_download
                result = yt_download(url)
                code = 200 if result.get("status") == "success" else 400
                self._set_headers(code)
                self.wfile.write(json.dumps(result).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

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

