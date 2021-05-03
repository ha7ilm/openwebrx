from owrx.controllers.session import SessionStorage
from owrx.users import UserList
from urllib import parse
from http.cookies import SimpleCookie

import logging

logger = logging.getLogger(__name__)


class Authentication(object):
    def getUser(self, request):
        if "owrx-session" not in request.cookies:
            return None
        session_id = request.cookies["owrx-session"].value
        storage = SessionStorage.getSharedInstance()
        session = storage.getSession(session_id)
        if session is None:
            return None
        if "user" not in session:
            return None
        userList = UserList.getSharedInstance()
        user = None
        try:
            user = userList[session["user"]]
            storage.prolongSession(session_id)
        except KeyError:
            pass
        return user


class AuthorizationMixin(object):
    def __init__(self, handler, request, options):
        self.authentication = Authentication()
        self.user = self.authentication.getUser(request)
        super().__init__(handler, request, options)

    def isAuthorized(self):
        return self.user is not None and self.user.is_enabled() and not self.user.must_change_password

    def handle_request(self):
        if self.isAuthorized():
            super().handle_request()
        else:
            cookie = SimpleCookie()
            cookie["owrx-session"] = ""
            cookie["owrx-session"]["expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
            self.set_response_cookies(cookie)
            if (
                "x-requested-with" in self.request.headers
                and self.request.headers["x-requested-with"] == "XMLHttpRequest"
            ):
                self.send_response("{}", code=403)
            else:
                target = "{}login?{}".format(self.get_document_root(), parse.urlencode({"ref": self.request.path[1:]}))
                self.send_redirect(target)
