from abc import ABC, abstractmethod
from owrx.modes import Modes
from owrx.config import Config
from owrx.form.converter import Converter, NullConverter, IntConverter, FloatConverter, EnumConverter
from enum import Enum


class Input(ABC):
    def __init__(self, id, label, infotext=None, converter: Converter = None, disabled=False, removable=False):
        self.id = id
        self.label = label
        self.infotext = infotext
        self.converter = self.defaultConverter() if converter is None else converter
        self.disabled = disabled
        self.removable = removable

    def setDisabled(self, disabled=True):
        self.disabled = disabled

    def setRemovable(self, removable=True):
        self.removable = removable

    def defaultConverter(self):
        return NullConverter()

    def bootstrap_decorate(self, input):
        infotext = "<small>{text}</small>".format(text=self.infotext) if self.infotext else ""
        return """
            <div class="form-group row" data-field="{id}">
                <label class="col-form-label col-form-label-sm col-3" for="{id}">{label}</label>
                <div class="col-9 p-0 removable-group {removable}">
                    <div class="removable-item">
                        {input}
                        {infotext}
                    </div>
                    {removebutton}
                </div>
            </div>
        """.format(
            id=self.id,
            label=self.label,
            input=input,
            infotext=infotext,
            removable="removable" if self.removable else "",
            removebutton='<button class="btn btn-sm btn-danger option-remove-button">Remove</button>'
            if self.removable
            else "",
        )

    def input_classes(self):
        return " ".join(["form-control", "form-control-sm"])

    def input_properties(self, value):
        props = {
            "class": self.input_classes(),
            "id": self.id,
            "name": self.id,
            "placeholder": self.label,
            "value": value,
        }
        if self.disabled:
            props["disabled"] = "disabled"
        return props

    def render_input_properties(self, value):
        return " ".join('{}="{}"'.format(prop, value) for prop, value in self.input_properties(value).items())

    def render_input(self, value):
        return "<input {properties} />".format(properties=self.render_input_properties(value))

    def render(self, config):
        value = config[self.id] if self.id in config else None
        return self.bootstrap_decorate(self.render_input(self.converter.convert_to_form(value)))

    def parse(self, data):
        return {self.id: self.converter.convert_from_form(data[self.id][0])} if self.id in data else {}

    def getLabel(self):
        return self.label


class TextInput(Input):
    def input_properties(self, value):
        props = super().input_properties(value)
        props["type"] = "text"
        return props


class NumberInput(Input):
    def __init__(self, id, label, infotext=None, append="", converter: Converter = None):
        super().__init__(id, label, infotext, converter=converter)
        self.step = None
        self.append = append

    def defaultConverter(self):
        return IntConverter()

    def input_properties(self, value):
        props = super().input_properties(value)
        props["type"] = "number"
        if self.step:
            props["step"] = self.step
        return props

    def render_input(self, value):
        if self.append:
            append = """
                <div class="input-group-append">
                    <span class="input-group-text">{append}</span>
                </div>
            """.format(
                append=self.append
            )
        else:
            append = ""

        return """
            <div class="input-group input-group-sm">
                {input}
                {append}
            </div>
        """.format(
            input=super().render_input(value),
            append=append,
        )


class FloatInput(NumberInput):
    def __init__(self, id, label, infotext=None, converter: Converter = None):
        super().__init__(id, label, infotext, converter=converter)
        self.step = "any"

    def defaultConverter(self):
        return FloatConverter()


class LocationInput(Input):
    def render_input(self, value):
        return """
            <div class="row">
                {inputs}
            </div>
            <div class="row">
                <div class="col map-input" data-key="{key}" for="{id}"></div>
            </div>
        """.format(
            id=self.id,
            inputs="".join(self.render_sub_input(value, id) for id in ["lat", "lon"]),
            key=Config.get()["google_maps_api_key"],
        )

    def render_sub_input(self, value, id):
        return """
            <div class="col">
                <input type="number" class="{classes}" id="{id}" name="{id}" placeholder="{label}" value="{value}"
                step="any" {disabled}>
            </div>
        """.format(
            id="{0}-{1}".format(self.id, id),
            label=self.label,
            classes=self.input_classes(),
            value=value[id],
            disabled="disabled" if self.disabled else "",
        )

    def parse(self, data):
        return {self.id: {k: float(data["{0}-{1}".format(self.id, k)][0]) for k in ["lat", "lon"]}}


class TextAreaInput(Input):
    def render_input(self, value):
        return """
            <textarea class="{classes}" id="{id}" name="{id}" style="height:200px;" {disabled}>{value}</textarea>
        """.format(
            id=self.id, classes=self.input_classes(), value=value, disabled="disabled" if self.disabled else ""
        )


class CheckboxInput(Input):
    def __init__(self, id, checkboxText, infotext=None, converter: Converter = None):
        super().__init__(id, "", infotext=infotext, converter=converter)
        self.checkboxText = checkboxText

    def render_input(self, value):
        return """
            <div class="{classes}">
                <input type="hidden" name="{id}" value="0" {disabled}>
                <input class="form-check-input" type="checkbox" id="{id}" name="{id}" value="1" {checked} {disabled}>
                <label class="form-check-label" for="{id}">
                    {checkboxText}
                </label>
            </div>
        """.format(
            id=self.id,
            classes=self.input_classes(),
            checked="checked" if value else "",
            disabled="disabled" if self.disabled else "",
            checkboxText=self.checkboxText,
        )

    def input_classes(self):
        return " ".join(["form-check", "form-control-sm"])

    def parse(self, data):
        if self.id in data:
            return {self.id: self.converter.convert_from_form("1" in data[self.id])}
        return {}

    def getLabel(self):
        return self.checkboxText


class Option(object):
    # used for both MultiCheckboxInput and DropdownInput
    def __init__(self, value, text):
        self.value = value
        self.text = text


class MultiCheckboxInput(Input):
    def __init__(self, id, label, options, infotext=None):
        super().__init__(id, label, infotext=infotext)
        self.options = options

    def render_input(self, value):
        return "".join(self.render_checkbox(o, value) for o in self.options)

    def checkbox_id(self, option):
        return "{0}-{1}".format(self.id, option.value)

    def render_checkbox(self, option, value):
        return """
          <div class="{classes}">
            <input class="form-check-input" type="checkbox" id="{id}" name="{id}" {checked} {disabled}>
            <label class="form-check-label" for="{id}">
              {checkboxText}
            </label>
          </div>
        """.format(
            id=self.checkbox_id(option),
            classes=self.input_classes(),
            checked="checked" if option.value in value else "",
            checkboxText=option.text,
            disabled="disabled" if self.disabled else "",
        )

    def parse(self, data):
        def in_response(option):
            boxid = self.checkbox_id(option)
            return boxid in data and data[boxid][0] == "on"

        return {self.id: [o.value for o in self.options if in_response(o)]}

    def input_classes(self):
        return " ".join(["form-check", "form-control-sm"])


class ServicesCheckboxInput(MultiCheckboxInput):
    def __init__(self, id, label, infotext=None):
        services = [Option(s.modulation, s.name) for s in Modes.getAvailableServices()]
        super().__init__(id, label, services, infotext)


class Js8ProfileCheckboxInput(MultiCheckboxInput):
    def __init__(self, id, label, infotext=None):
        profiles = [
            Option("normal", "Normal (15s, 50Hz, ~16WPM)"),
            Option("slow", "Slow (30s, 25Hz, ~8WPM"),
            Option("fast", "Fast (10s, 80Hz, ~24WPM"),
            Option("turbo", "Turbo (6s, 160Hz, ~40WPM"),
        ]
        super().__init__(id, label, profiles, infotext)


class DropdownInput(Input):
    def __init__(self, id, label, options, infotext=None, converter: Converter = None):
        try:
            isEnum = issubclass(options, DropdownEnum)
        except TypeError:
            isEnum = False
        if isEnum:
            self.options = [o.toOption() for o in options]
            if converter is None:
                converter = EnumConverter(options)
        else:
            self.options = options
        super().__init__(id, label, infotext=infotext, converter=converter)

    def render_input(self, value):
        return """
            <select class="{classes}" id="{id}" name="{id}" {disabled}>{options}</select>
        """.format(
            classes=self.input_classes(),
            id=self.id,
            options=self.render_options(value),
            disabled="disabled" if self.disabled else "",
        )

    def render_options(self, value):
        options = [
            """
                <option value="{value}" {selected}>{text}</option>
            """.format(
                text=o.text,
                value=o.value,
                selected="selected" if o.value == value else "",
            )
            for o in self.options
        ]
        return "".join(options)


class DropdownEnum(Enum):
    def toOption(self):
        return Option(self.name, str(self))


class ModesInput(DropdownInput):
    def __init__(self, id, label):
        options = [Option(m.modulation, m.name) for m in Modes.getAvailableModes()]
        super().__init__(id, label, options)


class FrequencyInput(Input):
    def __init__(self, id, label, infotext=None):
        super().__init__(id, label, infotext=infotext)

    def defaultConverter(self):
        return IntConverter()

    def input_properties(self, value):
        props = super().input_properties(value)
        props["type"] = "number"
        props["step"] = "any"
        return props

    def render_input(self, value):
        append = """
            <div class="input-group-append">
                <select class="input-group-text frequency-exponent" name="{id}-exponent" {disabled}>
                    <option value="0" selected>Hz</option>
                    <option value="3">kHz</option>
                    <option value="6">MHz</option>
                    <option value="9">GHz</option>
                    <option value="12">THz</option>
                </select>
            </div>
        """.format(
            id=self.id,
            disabled="disabled" if self.disabled else "",
        )

        return """
            <div class="input-group input-group-sm frequency-input">
                {input}
                {append}
            </div>
        """.format(
            input=super().render_input(value),
            append=append,
        )

    def parse(self, data):
        exponent_id = "{}-exponent".format(self.id)
        if self.id in data and exponent_id in data:
            value = int(float(data[self.id][0]) * 10 ** int(data[exponent_id][0]))
            return {self.id: value}
        return {}
