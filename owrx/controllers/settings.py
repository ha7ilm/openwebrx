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

    def validate(self, data):
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


class SettingsController(AdminController):
    inputs = [
        TextInput("receiver_name", "Receiver name"),
        TextInput("receiver_location", "Receiver location"),
        TextInput("receiver_asl", "Receiver elevation", infotext="Elevation in meters above mean see level"),
        TextInput("receiver_admin", "Receiver admin"),
        LocationInput("receiver_gps", "Receiver coordinates"),
        TextInput("photo_title", "Photo title"),
        TextAreaInput("photo_desc", "Photo description")
    ]

    def indexAction(self):
        self.serve_template("admin.html", **self.template_variables())

    def render_form(self):
        config = Config.get()
        inputs = "".join([i.render(config) for i in SettingsController.inputs])
        return """
            <form class="settings-body" method="POST">
                {inputs}
                <div class="buttons">
                    <button type="submit" class="btn btn-primary">Apply</button>
                </div>
            </form>
        """.format(inputs=inputs)

    def template_variables(self):
        variables = super().template_variables()
        variables["form"] = self.render_form()
        return variables

    def processFormData(self):
        data = parse_qs(self.get_body().decode("utf-8"))
        data = {k: v for i in SettingsController.inputs for k, v in i.validate(data).items()}
        config = Config.get()
        for k, v in data.items():
            config[k] = v
        self.send_redirect("/admin")
