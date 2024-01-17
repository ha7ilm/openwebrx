from owrx.config import Config
from owrx.controllers.admin import AuthorizationMixin
from owrx.controllers.template import WebpageController
from owrx.breadcrumb import Breadcrumb, BreadcrumbItem, BreadcrumbMixin
from abc import ABCMeta, abstractmethod
from urllib.parse import parse_qs

import logging

logger = logging.getLogger(__name__)


class SettingsController(AuthorizationMixin, WebpageController):
    def indexAction(self):
        self.serve_template("settings.html", **self.template_variables())


class SettingsFormController(AuthorizationMixin, BreadcrumbMixin, WebpageController, metaclass=ABCMeta):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.errors = {}
        self.globalError = None
        self.formData = None

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

    def buildRenderData(self):
        # this basially builds an intermediate result to be rendered
        # relevant when the form has to be displayed again due to errors
        # in this specific scenario, we mix the config with the data the user already submitted
        # we use a copy of the config so that whatever we apply here does not get accidentally stored
        res = self.getData().__dict__()
        if self.formData is not None:
            self._applyConfigData(res, self.formData)
        return res

    def render_sections(self):
        sections = "".join(section.render(self.buildRenderData(), self.getErrors()) for section in self.getSections())
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
        variables["error"] = self.renderGlobalError()
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
        data = None
        errors = None
        try:
            data, errors = self.parseFormData()
        except Exception as e:
            logger.exception("Error while parsing form data")
            self.globalError = str(e)
            return self.indexAction()

        self.formData = data
        if errors:
            self.errors = self._mergeErrors(errors)
            return self.indexAction()
        try:
            self.processData(data)
            self.store()
            self.send_redirect(self.getSuccessfulRedirect())
        except Exception as e:
            logger.exception("Error while processing form data")
            self.globalError = str(e)
            return self.indexAction()

    def _applyConfigData(self, dest, data):
        for k, v in data.items():
            if v is None:
                if k in dest:
                    del dest[k]
            else:
                dest[k] = v

    def processData(self, data):
        config = self.getData()
        self._applyConfigData(config, data)

    def store(self):
        Config.get().store()

    def buildModal(self):
        return ""

    def renderGlobalError(self):
        if self.globalError is None:
            return ""

        return """
            <div class="card text-white bg-danger">
                <div class="card-header">Error</div>
                <div class="card-body">
                    <div>Your settings could not be saved due to an error:</div>
                    <div>{error}</div>
                </div>
            </div>
        """.format(
            error=self.globalError
        )


class SettingsBreadcrumb(Breadcrumb):
    def __init__(self):
        super().__init__([])
        self.append(BreadcrumbItem("Settings", "settings"))
