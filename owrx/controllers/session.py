from .template import WebpageController


class SessionController(WebpageController):
    def loginAction(self):
        self.serve_template("login.html", **self.template_variables())

    def processLoginAction(self):
        self.send_redirect("/")

    def logoutAction(self):
        self.send_redirect("logout happening here")
