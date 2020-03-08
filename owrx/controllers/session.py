from .template import WebpageController
from urllib.parse import parse_qs
from uuid import uuid4
from http.cookies import SimpleCookie


class SessionStorage(object):
    sharedInstance = None

    @staticmethod
    def getSharedInstance():
        if SessionStorage.sharedInstance is None:
            SessionStorage.sharedInstance = SessionStorage()
        return SessionStorage.sharedInstance

    def __init__(self):
        self.sessions = {}

    def generateKey(self):
        return str(uuid4())

    def startSession(self, data):
        key = self.generateKey()
        self.updateSession(key, data)
        return key

    def getSession(self, key):
        if key not in self.sessions:
            return None
        return self.sessions[key]

    def updateSession(self, key, data):
        self.sessions[key] = data


class SessionController(WebpageController):
    def loginAction(self):
        self.serve_template("login.html", **self.template_variables())

    def processLoginAction(self):
        data = parse_qs(self.get_body().decode("utf-8"))
        data = {k: v[0] for k, v in data.items()}
        if "user" in data and "password" in data:
            # TODO actually check user and password
            if data["user"] == "admin" and data["password"] == "password":
                # TODO pass the final destination
                key = SessionStorage.getSharedInstance().startSession({"user": data["user"]})
                cookie = SimpleCookie()
                cookie["owrx-session"] = key
                self.send_redirect("/admin", cookies=cookie)
            else:
                self.send_redirect("/login")
        else:
            self.send_response("invalid request", code=400)

    def logoutAction(self):
        self.send_redirect("logout happening here")
