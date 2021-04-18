from owrx.controllers.template import WebpageController
from owrx.breadcrumb import Breadcrumb, BreadcrumbItem, BreadcrumbMixin
from owrx.controllers.settings import SettingsBreadcrumb


class FeatureController(BreadcrumbMixin, WebpageController):
    def get_breadcrumb(self) -> Breadcrumb:
        return SettingsBreadcrumb().append(BreadcrumbItem("Feature report", "features"))

    def indexAction(self):
        self.serve_template("features.html", **self.template_variables())
