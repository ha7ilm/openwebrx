from owrx.controllers import (
    StatusController,
    IndexController,
    AssetsController,
    WebSocketController,
    MapController,
    FeatureController,
    ApiController,
    MetricsController,
)
from http.server import BaseHTTPRequestHandler
import re
from urllib.parse import urlparse, parse_qs

import logging

logger = logging.getLogger(__name__)


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.router = Router()
        super().__init__(request, client_address, server)

    def do_GET(self):
        self.router.route(self)


class Request(object):
    def __init__(self, query=None, matches=None):
        self.query = query
        self.matches = matches


class Router(object):
    mappings = [
        {"route": "/", "controller": IndexController},
        {"route": "/status", "controller": StatusController},
        {"regex": "/static/(.+)", "controller": AssetsController},
        {"route": "/ws/", "controller": WebSocketController},
        {"regex": "(/favicon.ico)", "controller": AssetsController},
        # backwards compatibility for the sdr.hu portal
        {"regex": "/(gfx/openwebrx-avatar.png)", "controller": AssetsController},
        {"route": "/map", "controller": MapController},
        {"route": "/features", "controller": FeatureController},
        {"route": "/api/features", "controller": ApiController},
        {"route": "/metrics", "controller": MetricsController},
    ]

    def find_controller(self, path):
        for m in Router.mappings:
            if "route" in m:
                if m["route"] == path:
                    return (m["controller"], None)
            if "regex" in m:
                regex = re.compile(m["regex"])
                matches = regex.match(path)
                if matches:
                    return (m["controller"], matches)

    def route(self, handler):
        url = urlparse(handler.path)
        res = self.find_controller(url.path)
        if res is not None:
            (controller, matches) = res
            query = parse_qs(url.query)
            request = Request(query, matches)
            controller(handler, request).handle_request()
        else:
            handler.send_error(404, "Not Found", "The page you requested could not be found.")
