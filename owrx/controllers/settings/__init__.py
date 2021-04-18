from owrx.config import Config
from owrx.controllers.admin import AuthorizationMixin
from owrx.controllers.template import WebpageController
from owrx.form.error import FormError
from abc import ABCMeta, abstractmethod
from urllib.parse import parse_qs


class Section(object):
    def __init__(self, title, *inputs):
        self.title = title
        self.inputs = inputs

    def render_input(self, input, data, errors):
        return input.render(data, errors)

    def render_inputs(self, data, errors):
        return "".join([self.render_input(i, data, errors) for i in self.inputs])

    def classes(self):
        return ["col-12", "settings-section"]

    def render(self, data, errors):
        return """
            <div class="{classes}">
                <h3 class="settings-header">
                    {title}
                </h3>
                {inputs}
            </div>
        """.format(
            classes=" ".join(self.classes()), title=self.title, inputs=self.render_inputs(data, errors)
        )

    def parse(self, data):
        parsed_data = {}
        errors = []
        for i in self.inputs:
            try:
                parsed_data.update(i.parse(data))
            except FormError as e:
                errors.append(e)
            except Exception as e:
                errors.append(FormError(i.id, "{}: {}".format(type(e).__name__, e)))
        return parsed_data, errors


class SettingsController(AuthorizationMixin, WebpageController):
    def indexAction(self):
        self.serve_template("settings.html", **self.template_variables())


class SettingsFormController(AuthorizationMixin, WebpageController, metaclass=ABCMeta):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.errors = {}

    @abstractmethod
    def getSections(self):
        pass

    @abstractmethod
    def getTitle(self):
        pass

    def getData(self):
        return Config.get()

    def getErrors(self):
        return self.errors

    def render_sections(self):
        sections = "".join(section.render(self.getData(), self.getErrors()) for section in self.getSections())
        buttons = self.render_buttons()
        return """
            <form class="settings-body" method="POST">
                {sections}
                <div class="buttons container">
                    {buttons}
                </div>
            </form>
        """.format(
            sections=sections,
            buttons=buttons,
        )

    def render_buttons(self):
        return """
            <button type="submit" class="btn btn-primary">Apply and save</button>
        """

    def indexAction(self):
        self.serve_template("settings/general.html", **self.template_variables())

    def template_variables(self):
        variables = super().template_variables()
        variables["content"] = self.render_sections()
        variables["title"] = self.getTitle()
        variables["modal"] = self.buildModal()
        return variables

    def parseFormData(self):
        data = parse_qs(self.get_body().decode("utf-8"), keep_blank_values=True)
        result = {}
        errors = []
        for section in self.getSections():
            section_data, section_errors = section.parse(data)
            result.update(section_data)
            errors += section_errors
        return result, errors

    def getSuccessfulRedirect(self):
        return self.get_document_root() + self.request.path[1:]

    def _mergeErrors(self, errors):
        result = {}
        for e in errors:
            if e.getKey() not in result:
                result[e.getKey()] = []
            result[e.getKey()].append(e.getMessage())
        return result

    def processFormData(self):
        data, errors = self.parseFormData()
        if errors:
            self.errors = self._mergeErrors(errors)
            self.indexAction()
        else:
            self.processData(data)
            self.store()
            self.send_redirect(self.getSuccessfulRedirect())

    def processData(self, data):
        config = self.getData()
        for k, v in data.items():
            if v is None:
                if k in config:
                    del config[k]
            else:
                config[k] = v

    def store(self):
        Config.get().store()

    def buildModal(self):
        return ""
