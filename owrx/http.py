from owrx.controllers import (
    StatusController,
    IndexController,
    OwrxAssetsController,
    WebSocketController,
    MapController,
    FeatureController,
    ApiController,
    MetricsController,
    AprsSymbolsController,
)
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import re

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.router = Router()
        super().__init__(request, client_address, server)

    def log_message(self, format, *args):
        logger.debug("%s - - [%s] %s", self.address_string(), self.log_date_time_string(), format % args)

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
        {"regex": "/static/(.+)", "controller": OwrxAssetsController},
        {"regex": "/aprs-symbols/(.+)", "controller": AprsSymbolsController},
        {"route": "/ws/", "controller": WebSocketController},
        {"regex": "(/favicon.ico)", "controller": OwrxAssetsController},
        # backwards compatibility for the sdr.hu portal
        {"regex": "/(gfx/openwebrx-avatar.png)", "controller": OwrxAssetsController},
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
