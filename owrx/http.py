from owrx.controllers.status import StatusController
from owrx.controllers.template import IndexController, MapController
from owrx.controllers.feature import FeatureController
from owrx.controllers.assets import OwrxAssetsController, AprsSymbolsController, CompiledAssetsController
from owrx.controllers.websocket import WebSocketController
from owrx.controllers.api import ApiController
from owrx.controllers.metrics import MetricsController
from owrx.controllers.settings import SettingsController
from owrx.controllers.settings.general import GeneralSettingsController
from owrx.controllers.settings.sdr import (
    SdrDeviceListController,
    SdrDeviceController,
    SdrProfileController,
    NewSdrDeviceController,
    NewProfileController,
)
from owrx.controllers.settings.reporting import ReportingController
from owrx.controllers.settings.backgrounddecoding import BackgroundDecodingController
from owrx.controllers.settings.decoding import DecodingSettingsController
from owrx.controllers.settings.bookmarks import BookmarksController
from owrx.controllers.session import SessionController
from owrx.controllers.profile import ProfileController
from owrx.controllers.imageupload import ImageUploadController
from owrx.controllers.robots import RobotsController
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import re
from abc import ABC, abstractmethod
from http.cookies import SimpleCookie

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Request(object):
    def __init__(self, url, method, headers):
        parsed_url = urlparse(url)
        self.path = parsed_url.path
        self.query = parse_qs(parsed_url.query)
        self.matches = None
        self.method = method
        self.headers = headers
        self.cookies = SimpleCookie()
        if "Cookie" in headers:
            self.cookies.load(headers["Cookie"])

    def setMatches(self, matches):
        self.matches = matches


class Route(ABC):
    def __init__(self, controller, method="GET", options=None):
        self.controller = controller
        self.controllerOptions = options if options is not None else {}
        self.method = method

    @abstractmethod
    def matches(self, request):
        pass


class StaticRoute(Route):
    def __init__(self, route, controller, method="GET", options=None):
        self.route = route
        super().__init__(controller, method, options)

    def matches(self, request):
        return request.path == self.route and self.method == request.method


class RegexRoute(Route):
    def __init__(self, regex, controller, method="GET", options=None):
        self.regex = re.compile(regex)
        super().__init__(controller, method, options)

    def matches(self, request):
        matches = self.regex.match(request.path)
        # this is probably not the cleanest way to do it...
        request.setMatches(matches)
        return matches is not None and self.method == request.method


class Router(object):
    def __init__(self):
        self.routes = [
            StaticRoute("/", IndexController),
            StaticRoute("/robots.txt", RobotsController),
            StaticRoute("/status.json", StatusController),
            RegexRoute("^/static/(.+)$", OwrxAssetsController),
            RegexRoute("^/compiled/(.+)$", CompiledAssetsController),
            RegexRoute("^/aprs-symbols/(.+)$", AprsSymbolsController),
            StaticRoute("/ws/", WebSocketController),
            RegexRoute("^(/favicon.ico)$", OwrxAssetsController),
            StaticRoute("/map", MapController),
            StaticRoute("/features", FeatureController),
            StaticRoute("/api/features", ApiController),
            StaticRoute("/metrics", MetricsController, options={"action": "prometheusAction"}),
            StaticRoute("/metrics.json", MetricsController),
            StaticRoute("/settings", SettingsController),
            StaticRoute("/settings/general", GeneralSettingsController),
            StaticRoute(
                "/settings/general", GeneralSettingsController, method="POST", options={"action": "processFormData"}
            ),
            StaticRoute("/settings/sdr", SdrDeviceListController),
            StaticRoute("/settings/newsdr", NewSdrDeviceController),
            StaticRoute(
                "/settings/newsdr", NewSdrDeviceController, method="POST", options={"action": "processFormData"}
            ),
            RegexRoute("^/settings/sdr/([^/]+)$", SdrDeviceController),
            RegexRoute(
                "^/settings/sdr/([^/]+)$", SdrDeviceController, method="POST", options={"action": "processFormData"}
            ),
            RegexRoute("^/settings/deletesdr/([^/]+)$", SdrDeviceController, options={"action": "deleteDevice"}),
            RegexRoute("^/settings/sdr/([^/]+)/newprofile$", NewProfileController),
            RegexRoute(
                "^/settings/sdr/([^/]+)/newprofile$",
                NewProfileController,
                method="POST",
                options={"action": "processFormData"},
            ),
            RegexRoute("^/settings/sdr/([^/]+)/profile/([^/]+)$", SdrProfileController),
            RegexRoute(
                "^/settings/sdr/([^/]+)/profile/([^/]+)$",
                SdrProfileController,
                method="POST",
                options={"action": "processFormData"},
            ),
            RegexRoute(
                "^/settings/sdr/([^/]+)/deleteprofile/([^/]+)$",
                SdrProfileController,
                options={"action": "deleteProfile"},
            ),
            StaticRoute("/settings/bookmarks", BookmarksController),
            StaticRoute("/settings/bookmarks", BookmarksController, method="POST", options={"action": "new"}),
            RegexRoute("^/settings/bookmarks/(.+)$", BookmarksController, method="POST", options={"action": "update"}),
            RegexRoute(
                "^/settings/bookmarks/(.+)$", BookmarksController, method="DELETE", options={"action": "delete"}
            ),
            StaticRoute("/settings/reporting", ReportingController),
            StaticRoute(
                "/settings/reporting", ReportingController, method="POST", options={"action": "processFormData"}
            ),
            StaticRoute("/settings/backgrounddecoding", BackgroundDecodingController),
            StaticRoute(
                "/settings/backgrounddecoding",
                BackgroundDecodingController,
                method="POST",
                options={"action": "processFormData"},
            ),
            StaticRoute("/settings/decoding", DecodingSettingsController),
            StaticRoute(
                "/settings/decoding", DecodingSettingsController, method="POST", options={"action": "processFormData"}
            ),
            StaticRoute("/login", SessionController, options={"action": "loginAction"}),
            StaticRoute("/login", SessionController, method="POST", options={"action": "processLoginAction"}),
            StaticRoute("/logout", SessionController, options={"action": "logoutAction"}),
            StaticRoute("/pwchange", ProfileController),
            StaticRoute("/pwchange", ProfileController, method="POST", options={"action": "processPwChange"}),
            StaticRoute("/imageupload", ImageUploadController),
            StaticRoute("/imageupload", ImageUploadController, method="POST", options={"action": "processImage"}),
        ]

    def find_route(self, request):
        for r in self.routes:
            if r.matches(request):
                return r

    def route(self, handler, request):
        route = self.find_route(request)
        if route is not None:
            controller = route.controller
            controller(handler, request, route.controllerOptions).handle_request()
        else:
            handler.send_error(404, "Not Found", "The page you requested could not be found.")


class RequestHandler(BaseHTTPRequestHandler):
    timeout = 30
    router = Router()

    def log_message(self, format, *args):
        logger.debug("%s - - [%s] %s", self.address_string(), self.log_date_time_string(), format % args)

    def do_GET(self):
        self.router.route(self, self._build_request("GET"))

    def do_POST(self):
        self.router.route(self, self._build_request("POST"))

    def do_DELETE(self):
        self.router.route(self, self._build_request("DELETE"))

    def _build_request(self, method):
        return Request(self.path, method, self.headers)
