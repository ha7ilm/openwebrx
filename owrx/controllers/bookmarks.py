from owrx.controllers.template import WebpageController
from owrx.controllers.admin import AuthorizationMixin


class BookmarksController(AuthorizationMixin, WebpageController):
    def header_variables(self):
        variables = super().header_variables()
        variables["assets_prefix"] = "../"
        return variables

    def indexAction(self):
        self.serve_template("settings/bookmarks.html", **self.template_variables())
