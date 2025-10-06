import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from app.config import config
from app.routes.basic_routes import home, health
from app.routes.yt_details import yt_details
from app.routes.yt_thumbnail import get_thumbnail_url
from app.routes.yt_download import yt_download, yt_download_streaming
import socket
from app.utils.boot_check import perform_boot_check


class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200, content_type='application/json'):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.end_headers()

    def do_GET(self):
        if self.path == '/':
            self._set_headers()
            self.wfile.write(json.dumps(home()).encode())
        elif self.path == '/health':
            self._set_headers()
            self.wfile.write(json.dumps(health()).encode())
        elif self.path.startswith('/yt_details'):
            query = parse_qs(urlparse(self.path).query)
            url = query.get('url', [None])[0]
            if not url:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'url' parameter"}).encode())
            else:
                self._set_headers()
                self.wfile.write(json.dumps(yt_details(url)).encode())
        elif self.path.startswith('/yt_thumbnail'):
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
            query = parse_qs(urlparse(self.path).query)
            url = query.get('url', [None])[0]
            stream = query.get('stream', ['false'])[0].lower() == 'true'
            binary = query.get('binary', ['false'])[0].lower() == 'true'

            if not url:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "Missing 'url' query parameter."
                }).encode())
            else:
                if stream:
                    # Stream progress via Server-Sent Events
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Cache-Control', 'no-cache')
                    self.send_header('Connection', 'keep-alive')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()

                    try:
                        for event in yt_download_streaming(url, return_binary=binary):
                            self.wfile.write(event.encode('utf-8'))
                            self.wfile.flush()
                    except Exception as e:
                        error_event = f"event: error\ndata: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
                        self.wfile.write(error_event.encode('utf-8'))
                        self.wfile.flush()
                else:
                    # Regular non-streaming download
                    result = yt_download(url, return_binary=binary)
                    
                    # If binary is requested and available, return video file directly
                    if binary and result.get("status") == "success" and "video_bytes" in result:
                        from urllib.parse import quote
                        filename = result["file"]["name"]
                        # Encode filename for Content-Disposition header (RFC 5987)
                        encoded_filename = quote(filename)
                        
                        self.send_response(200)
                        self.send_header('Content-Type', result.get("content_type", "video/mp4"))
                        self.send_header('Content-Disposition', f'attachment; filename*=UTF-8\'\'{encoded_filename}')
                        self.end_headers()
                        self.wfile.write(result["video_bytes"])
                    else:
                        # Return JSON response
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

