from owrx.controllers import Controller
from owrx.details import ReceiverDetails
from string import Template
import pkg_resources


class TemplateController(Controller):
    def render_template(self, file, **vars):
        file_content = pkg_resources.resource_string("htdocs", file).decode("utf-8")
        template = Template(file_content)

        return template.safe_substitute(**vars)

    def serve_template(self, file, **vars):
        self.send_response(self.render_template(file, **vars), content_type="text/html")

    def default_variables(self):
        return {}


class WebpageController(TemplateController):
    def get_document_root(self):
        path_parts = [part for part in self.request.path[1:].split("/")]
        levels = max(0, len(path_parts) - 1)
        return "../" * levels

    def header_variables(self):
        variables = {"document_root": self.get_document_root()}
        variables.update(ReceiverDetails().__dict__())
        return variables

    def template_variables(self):
        header = self.render_template("include/header.include.html", **self.header_variables())
        return {"header": header, "document_root": self.get_document_root()}


class IndexController(WebpageController):
    def indexAction(self):
        self.serve_template("index.html", **self.template_variables())


class MapController(WebpageController):
    def indexAction(self):
        # TODO check if we have a google maps api key first?
        self.serve_template("map.html", **self.template_variables())


class FeatureController(WebpageController):
    def indexAction(self):
        self.serve_template("features.html", **self.template_variables())
