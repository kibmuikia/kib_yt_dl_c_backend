# app/routes/route_handlers.py

import json
from typing import Dict, Any

from app.routes.basic_routes import home, health
from app.routes.yt_details import yt_details
from app.routes.yt_thumbnail import get_thumbnail_url
from app.routes.yt_download import yt_download, yt_download_streaming

QueryDict = Dict[str, Any]

class HandlerMixin:
    def write_json(self, obj: Any, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def handle_home(self, query: QueryDict) -> None:
        self.write_json(home())
    
    def handle_health(self, query: QueryDict) -> None:
        self.write_json(health())

    def handle_yt_details(self, query: QueryDict) -> None:
        url: str | None = query.get("url", [None])[0]
        if not url:
            self.write_json({
                "status": "error",
                "message": "Missing 'url' query parameter."
            }, 400)
        else:
            self.write_json(yt_details(url))

    def handle_yt_thumbnail(self, query: QueryDict) -> None:
        url = query.get("url", [None])[0]
        download_flag: bool = query.get("download", ["false"])[0].lower() == "true"
        if not url:
            self.write_json({
                "status": "error",
                "message": "Missing 'url' query parameter."
            }, 400)
        else:
            result: Dict[str, Any] = get_thumbnail_url(url, download=download_flag)
            if download_flag and result.get("status") == "success" and "image_bytes" in result:
                self.send_response(200)
                self.send_header("Content-type", "image/jpeg")
                self.end_headers()
                self.wfile.write(result["image_bytes"])
            else:
                code = 200 if result.get("status") == "success" else 400
                self.write_json(result, code)

    def handle_yt_download(self, query: QueryDict) -> None:
        url = query.get("url", [None])[0]
        stream: bool = query.get("stream", ["false"])[0].lower() == "true"
        if not url:
            self.write_json({
                "status": "error",
                "message": "Missing 'url' query parameter."
            }, 400)
        else:
            if stream:
                self.send_response(200)
                self.send_header("Content-type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                try:
                    for event in yt_download_streaming(url):
                        self.wfile.write(event.encode('utf-8'))
                        self.wfile.flush()
                except Exception as e:
                    error_event: str = f"event: error\ndata: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
                    self.wfile.write(error_event.encode('utf-8'))
                    self.wfile.flush()
            else:
                result: dict[str, Any] = yt_download(url)
                code = 200 if result.get("status") == "success" else 400
                self.write_json(result, code)

