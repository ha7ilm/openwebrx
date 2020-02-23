from . import Controller


class Authentication(object):
    def isAuthenticated(self, request):
        return False


class SettingsController(Controller):
    def __init__(self, handler, request, options):
        self.authentication = Authentication()
        super().__init__(handler, request, options)

    def handle_request(self):
        if self.authentication.isAuthenticated(self.request):
            super().handle_request()
        else:
            self.send_redirect("/login")

    def indexAction(self):
        self.send_response("actual content here")
