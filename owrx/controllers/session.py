from . import Controller


class SessionController(Controller):
    def loginAction(self):
        self.send_response("login happening here")

    def logoutAction(self):
        self.send_redirect("logout happening here")
