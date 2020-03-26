from abc import ABC, abstractmethod
from .admin import AdminController


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
    def render_input(self):
        pass

    def render(self):
        return self.bootstrap_decorate(self.render_input())


class TextInput(Input):
    def render_input(self):
        return """
            <input type="text" class="{classes}" id="{id}" name="{id}" placeholder="{label}">
        """.format(id=self.id, label=self.label, classes=self.input_classes())


class LocationInput(Input):
    def render_input(self):
        # TODO make this work and pretty
        return "Placeholder for a map widget to select receiver location"


class TextAreaInput(Input):
    def render_input(self):
        return """
            <textarea class="{classes}" id="{id}" name="{id}"></textarea>
        """.format(id=self.id, classes=self.input_classes())


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
        inputs = "".join([i.render() for i in SettingsController.inputs])
        return "<form class=\"settings-body\">{inputs}</form>".format(inputs=inputs)

    def template_variables(self):
        variables = super().template_variables()
        variables["form"] = self.render_form()
        return variables
