from .template import WebpageController
from urllib.parse import parse_qs
import logging

logger = logging.getLogger(__name__)


class SessionController(WebpageController):
    def loginAction(self):
        self.serve_template("login.html", **self.template_variables())

    def processLoginAction(self):
        data = parse_qs(self.get_body().decode("utf-8"))
        data = {k: v[0] for k, v in data.items()}
        logger.debug(data)
        if "user" in data and "password" in data:
            # TODO actually check user and password
            if data["user"] == "admin" and data["password"] == "password":
                # TODO pass the final destination
                # TODO actual session cookie
                self.send_redirect("/settings", cookies=["session-cookie"])
            else:
                self.send_redirect("/login")
        else:
            self.send_response("invalid request", code=400)

    def logoutAction(self):
        self.send_redirect("logout happening here")
