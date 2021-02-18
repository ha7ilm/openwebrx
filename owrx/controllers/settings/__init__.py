from owrx.config import Config
from owrx.controllers.admin import AuthorizationMixin
from owrx.controllers.template import WebpageController
from abc import ABCMeta, abstractmethod
from urllib.parse import parse_qs


class Section(object):
    def __init__(self, title, *inputs):
        self.title = title
        self.inputs = inputs

    def render_inputs(self):
        config = Config.get()
        return "".join([i.render(config) for i in self.inputs])

    def render(self):
        return """
            <div class="col-12 settings-section">
                <h3 class="settings-header">
                    {title}
                </h3>
                {inputs}
            </div>
        """.format(
            title=self.title, inputs=self.render_inputs()
        )

    def parse(self, data):
        return {k: v for i in self.inputs for k, v in i.parse(data).items()}


class SettingsController(AuthorizationMixin, WebpageController):
    def indexAction(self):
        self.serve_template("settings.html", **self.template_variables())


class SettingsFormController(AuthorizationMixin, WebpageController, metaclass=ABCMeta):
    @abstractmethod
    def getSections(self):
        pass

    @abstractmethod
    def getTitle(self):
        pass

    def render_sections(self):
        sections = "".join(section.render() for section in self.getSections())
        return """
            <form class="settings-body" method="POST">
                {sections}
                <div class="buttons">
                    <button type="submit" class="btn btn-primary">Apply</button>
                </div>
            </form>
        """.format(
            sections=sections
        )

    def indexAction(self):
        self.serve_template("settings/general.html", **self.template_variables())

    def header_variables(self):
        variables = super().header_variables()
        variables["assets_prefix"] = "../"
        return variables

    def template_variables(self):
        variables = super().template_variables()
        variables["content"] = self.render_sections()
        variables["title"] = self.getTitle()
        variables["assets_prefix"] = "../"
        return variables

    def parseFormData(self):
        data = parse_qs(self.get_body().decode("utf-8"), keep_blank_values=True)
        return {k: v for i in self.getSections() for k, v in i.parse(data).items()}

    def processFormData(self):
        self.processData(self.parseFormData())

    def processData(self, data):
        config = Config.get()
        for k, v in data.items():
            if v is None:
                if k in config:
                    del config[k]
            else:
                config[k] = v
        config.store()
        self.send_redirect(self.request.path)
