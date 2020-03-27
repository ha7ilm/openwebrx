from abc import ABC, abstractmethod
from .admin import AdminController
from owrx.config import Config
from urllib.parse import parse_qs
import logging

logger = logging.getLogger(__name__)


class Input(ABC):
    def __init__(self, id, label, infotext=None):
        self.id = id
        self.label = label
        self.infotext = infotext

    def bootstrap_decorate(self, input):
        infotext = "<small>{text}</small>".format(text=self.infotext) if self.infotext else ""
        return """
            <div class="form-group row">
                <label class="col-form-label col-form-label-sm col-3" for="{id}">{label}</label>
                <div class="col-9 p-0">
                    {input}
                    {infotext}
                </div>
            </div>
        """.format(id=self.id, label=self.label, input=input, infotext=infotext)

    def input_classes(self):
        return " ".join(["form-control", "form-control-sm"])

    @abstractmethod
    def render_input(self, value):
        pass

    def render(self, config):
        return self.bootstrap_decorate(self.render_input(config[self.id]))

    def parse(self, data):
        return {self.id: data[self.id][0]} if self.id in data else {}


class TextInput(Input):
    def render_input(self, value):
        return """
            <input type="text" class="{classes}" id="{id}" name="{id}" placeholder="{label}" value="{value}">
        """.format(id=self.id, label=self.label, classes=self.input_classes(), value=value)


class LocationInput(Input):
    def render_input(self, value):
        # TODO make this work and pretty
        return "Placeholder for a map widget to select receiver location"


class TextAreaInput(Input):
    def render_input(self, value):
        return """
            <textarea class="{classes}" id="{id}" name="{id}" style="height:200px;">{value}</textarea>
        """.format(id=self.id, classes=self.input_classes(), value=value)


class CheckboxInput(Input):
    def __init__(self, id, label, checkboxText, infotext=None):
        super().__init__(id, label, infotext=infotext)
        self.checkboxText = checkboxText

    def render_input(self, value):
        return """
          <div class="{classes}">
            <input class="form-check-input" type="checkbox" id="{id}" name="{id}" {checked}>
            <label class="form-check-label" for="{id}">
              {checkboxText}
            </label>
          </div>
        """.format(id=self.id, classes=self.input_classes(), checked="checked" if value else "", checkboxText=self.checkboxText)

    def input_classes(self):
        return " ".join(["form-check", "form-control-sm"])

    def parse(self, data):
        return {self.id: self.id in data and data[self.id][0] == "on"}


class Section(object):
    def __init__(self, title, *inputs):
        self.title = title
        self.inputs = inputs

    def render_inputs(self):
        config = Config.get()
        return "".join([i.render(config) for i in self.inputs])

    def render(self):
        return """
            <div class="col-12 settings-category">
                <h3 class="settings-header">
                    {title}
                </h3>
                {inputs}
            </div>
        """.format(title=self.title, inputs=self.render_inputs())

    def parse(self, data):
        return {k: v for i in self.inputs for k, v in i.parse(data).items()}


class SettingsController(AdminController):
    sections = [
        Section(
            "General Settings",
            TextInput("receiver_name", "Receiver name"),
            TextInput("receiver_location", "Receiver location"),
            TextInput("receiver_asl", "Receiver elevation", infotext="Elevation in meters above mean see level"),
            TextInput("receiver_admin", "Receiver admin"),
            LocationInput("receiver_gps", "Receiver coordinates"),
            TextInput("photo_title", "Photo title"),
            TextAreaInput("photo_desc", "Photo description"),
        ),
        Section(
            "sdr.hu",
            TextInput("sdrhu_key", "sdr.hu key", infotext="Please obtain your personal key on <a href=\"https://sdr.hu\">sdr.hu</a>"),
            CheckboxInput("sdrhu_public_listing", "List on sdr.hu", "List msy receiver on sdr.hu"),
            TextInput("server_hostname", "Hostname"),
        ),
    ]

    def render_sections(self):
        sections = "".join(section.render() for section in SettingsController.sections)
        return """
            <form class="settings-body" method="POST">
                {sections}
                <div class="buttons">
                    <button type="submit" class="btn btn-primary">Apply</button>
                </div>
            </form>
        """.format(sections=sections)

    def indexAction(self):
        self.serve_template("admin.html", **self.template_variables())

    def template_variables(self):
        variables = super().template_variables()
        variables["sections"] = self.render_sections()
        return variables

    def processFormData(self):
        data = parse_qs(self.get_body().decode("utf-8"))
        data = {k: v for i in SettingsController.sections for k, v in i.parse(data).items()}
        config = Config.get()
        for k, v in data.items():
            config[k] = v
        self.send_redirect("/admin")
