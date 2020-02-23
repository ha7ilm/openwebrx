from owrx.controllers.status import StatusController
from owrx.controllers.template import (
    IndexController,
    MapController,
    FeatureController
)
from owrx.controllers.assets import (
    OwrxAssetsController,
    AprsSymbolsController
)
from owrx.controllers.websocket import WebSocketController
from owrx.controllers.api import ApiController
from owrx.controllers.metrics import MetricsController
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import re
from abc import ABC, abstractmethod

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
    def __init__(self, url):
        self.path = url.path
        self.query = parse_qs(url.query)
        self.matches = None

    def setMatches(self, matches):
        self.matches = matches


class Route(ABC):
    def __init__(self, controller, controllerOptions = None):
        self.controller = controller
        self.controllerOptions = controllerOptions if controllerOptions is not None else {}

    @abstractmethod
    def matches(self, request):
        pass


class StaticRoute(Route):
    def __init__(self, route, controller, controllerOptions = None):
        self.route = route
        super().__init__(controller, controllerOptions)

    def matches(self, request):
        return request.path == self.route


class RegexRoute(Route):
    def __init__(self, regex, controller, controllerOptions = None):
        self.regex = re.compile(regex)
        super().__init__(controller, controllerOptions)

    def matches(self, request):
        matches = self.regex.match(request.path)
        # this is probably not the cleanest way to do it...
        request.setMatches(matches)
        return matches is not None


class Router(object):
    def __init__(self):
        self.routes = [
            StaticRoute("/", IndexController),
            StaticRoute("/status", StatusController),
            StaticRoute("/status.json", StatusController, {"action": "jsonAction"}),
            RegexRoute("/static/(.+)", OwrxAssetsController),
            RegexRoute("/aprs-symbols/(.+)", AprsSymbolsController),
            StaticRoute("/ws/", WebSocketController),
            RegexRoute("(/favicon.ico)", OwrxAssetsController),
            # backwards compatibility for the sdr.hu portal
            RegexRoute("(/gfx/openwebrx-avatar.png)", OwrxAssetsController),
            StaticRoute("/map", MapController),
            StaticRoute("/features", FeatureController),
            StaticRoute("/api/features", ApiController),
            StaticRoute("/metrics", MetricsController),
        ]

    def find_route(self, request):
        for r in self.routes:
            if r.matches(request):
                return r

    def route(self, handler):
        url = urlparse(handler.path)
        request = Request(url)
        route = self.find_route(request)
        if route is not None:
            controller = route.controller
            controller(handler, request, route.controllerOptions).handle_request()
        else:
            handler.send_error(404, "Not Found", "The page you requested could not be found.")
