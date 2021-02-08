from .template import WebpageController
from .session import SessionStorage
from owrx.config import Config
from owrx.users import UserList
from urllib import parse

import logging

logger = logging.getLogger(__name__)


class Authentication(object):
    def getUser(self, request):
        if "owrx-session" not in request.cookies:
            return None
        session = SessionStorage.getSharedInstance().getSession(request.cookies["owrx-session"].value)
        if session is None:
            return None
        if "user" not in session:
            return None
        userList = UserList.getSharedInstance()
        try:
            return userList[session["user"]]
        except KeyError:
            return None


class AdminController(WebpageController):
    def __init__(self, handler, request, options):
        self.authentication = Authentication()
        self.user = self.authentication.getUser(request)
        super().__init__(handler, request, options)

    def isAuthorized(self):
        return self.user is not None and self.user.is_enabled() and not self.user.must_change_password

    def handle_request(self):
        config = Config.get()
        if "webadmin_enabled" not in config or not config["webadmin_enabled"]:
            self.send_response("Web Admin is disabled", code=403)
            return
        if self.isAuthorized():
            super().handle_request()
        else:
            target = "/login?{0}".format(parse.urlencode({"ref": self.request.path}))
            self.send_redirect(target)
