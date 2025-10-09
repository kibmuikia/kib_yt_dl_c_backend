# app/routes.py

from typing import Callable, Dict, Any
from app.routes.route_handlers import HandlerMixin

HandlerFunc = Callable[[HandlerMixin, Dict[str, Any]], None]

route_table: Dict[str, HandlerFunc] = {
    '/': lambda handler, query: handler.handle_home(query),
    '/health': lambda handler, query: handler.handle_health(query),
    '/yt_details': lambda handler, query: handler.handle_yt_details(query),
    '/yt_thumbnail': lambda handler, query: handler.handle_yt_thumbnail(query),
    '/yt_download': lambda handler, query: handler.handle_yt_download(query)
}
