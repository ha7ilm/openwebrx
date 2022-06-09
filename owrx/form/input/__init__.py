from abc import ABC
from owrx.modes import Modes
from owrx.form.input.validator import Validator
from owrx.form.input.converter import Converter, NullConverter, IntConverter, FloatConverter, EnumConverter, TextConverter
from enum import Enum


class Input(ABC):
    def __init__(self, id, label, infotext=None, converter: Converter = None, validator: Validator = None, disabled=False, removable=False):
        self.id = id
        self.label = label
        self.infotext = infotext
        self.converter = self.defaultConverter() if converter is None else converter
        self.validator = validator
        self.disabled = disabled
        self.removable = removable

    def setDisabled(self, disabled=True):
        self.disabled = disabled

    def setRemovable(self, removable=True):
        self.removable = removable

    def defaultConverter(self):
        return NullConverter()

    def bootstrap_decorate(self, input):
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
            infotext="<small>{text}</small>".format(text=self.infotext) if self.infotext else "",
            removable="removable" if self.removable else "",
            removebutton='<button type="button" class="btn btn-sm btn-danger option-remove-button">Remove</button>'
            if self.removable
            else "",
        )

    def input_classes(self, errors):
        classes = ["form-control", "form-control-sm"]
        if errors:
            classes.append("is-invalid")
        return " ".join(classes)

    def input_properties(self, value, errors):
        props = {
            "class": self.input_classes(errors),
            "id": self.id,
            "name": self.id,
            "placeholder": self.label,
            "value": value,
        }
        if self.disabled:
            props["disabled"] = "disabled"
        return props

    def render_input_properties(self, value, error):
        return " ".join('{}="{}"'.format(prop, value) for prop, value in self.input_properties(value, error).items())

    def render_errors(self, errors):
        return "".join("""<div class="invalid-feedback">{msg}</div>""".format(msg=e) for e in errors)

    def render_input_group(self, value, errors):
        return """
            {input}
            {errors}
        """.format(
            input=self.render_input(value, errors),
            errors=self.render_errors(errors)
        )

    def render_input(self, value, errors):
        return "<input {properties} />".format(properties=self.render_input_properties(value, errors))

    def render(self, config, errors):
        value = config[self.id] if self.id in config else None
        error = errors[self.id] if self.id in errors else []
        return self.bootstrap_decorate(self.render_input_group(self.converter.convert_to_form(value), error))

    def parse(self, data):
        if self.id in data:
            value = self.converter.convert_from_form(data[self.id][0])
            if self.validator is not None:
                self.validator.validate(self.id, value)
            return {self.id: value}
        return {}

    def getLabel(self):
        return self.label


class TextInput(Input):
    def input_properties(self, value, errors):
        props = super().input_properties(value, errors)
        props["type"] = "text"
        return props

    def defaultConverter(self):
        return TextConverter()


class NumberInput(Input):
    def __init__(self, id, label, infotext=None, append="", converter: Converter = None, validator: Validator = None):
        super().__init__(id, label, infotext, converter=converter, validator=validator)
        self.step = None
        self.append = append

    def defaultConverter(self):
        return IntConverter()

    def input_properties(self, value, errors):
        props = super().input_properties(value, errors)
        props["type"] = "number"
        if self.step:
            props["step"] = self.step
        return props

    def render_input_group(self, value, errors):
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
                {errors}
            </div>
        """.format(
            input=self.render_input(value, errors),
            append=append,
            errors=self.render_errors(errors)
        )


class FloatInput(NumberInput):
    def __init__(self, id, label, infotext=None, converter: Converter = None):
        super().__init__(id, label, infotext, converter=converter)
        self.step = "any"

    def defaultConverter(self):
        return FloatConverter()


class TextAreaInput(Input):
    def render_input(self, value, errors):
        return """
            <textarea class="{classes}" id="{id}" name="{id}" style="height:200px;" {disabled}>{value}</textarea>
        """.format(
            id=self.id,
            classes=self.input_classes(errors),
            value=value,
            disabled="disabled" if self.disabled else "",
        )


class CheckboxInput(Input):
    def __init__(self, id, checkboxText, infotext=None, converter: Converter = None):
        super().__init__(id, "", infotext=infotext, converter=converter)
        self.checkboxText = checkboxText

    def render_input(self, value, errors):
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
            classes=self.input_classes(errors),
            checked="checked" if value else "",
            disabled="disabled" if self.disabled else "",
            checkboxText=self.checkboxText,
        )

    def input_classes(self, error):
        classes = ["form-check", "form-control-sm"]
        if error:
            classes.append("is-invalid")
        return " ".join(classes)

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

    def render_input(self, value, errors):
        return "".join(self.render_checkbox(o, value, errors) for o in self.options)

    def checkbox_id(self, option):
        return "{0}-{1}".format(self.id, option.value)

    def render_checkbox(self, option, value, errors):
        return """
          <div class="{classes}">
            <input class="form-check-input" type="checkbox" id="{id}" name="{id}" {checked} {disabled}>
            <label class="form-check-label" for="{id}">
              {checkboxText}
            </label>
          </div>
        """.format(
            id=self.checkbox_id(option),
            classes=self.input_classes(errors),
            checked="checked" if option.value in value else "",
            checkboxText=option.text,
            disabled="disabled" if self.disabled else "",
        )

    def parse(self, data):
        def in_response(option):
            boxid = self.checkbox_id(option)
            return boxid in data and data[boxid][0] == "on"

        return {self.id: [o.value for o in self.options if in_response(o)]}

    def input_classes(self, error):
        classes = ["form-check", "form-control-sm"]
        if error:
            classes.append("is-invalid")
        return " ".join(classes)


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

    def render_input(self, value, errors):
        return """
            <select class="{classes}" id="{id}" name="{id}" {disabled}>{options}</select>
        """.format(
            classes=self.input_classes(errors),
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


class ExponentialInput(Input):
    def __init__(self, id, label, unit, infotext=None):
        super().__init__(id, label, infotext=infotext)
        self.unit = unit

    def defaultConverter(self):
        return IntConverter()

    def input_properties(self, value, errors):
        props = super().input_properties(value, errors)
        props["type"] = "number"
        props["step"] = "any"
        return props

    def render_input_group(self, value, errors):
        append = """
            <div class="input-group-append">
                <select class="input-group-text exponent" name="{id}-exponent" tabindex="-1" {disabled}>
                    <option value="0" selected>{unit}</option>
                    <option value="3">k{unit}</option>
                    <option value="6">M{unit}</option>
                    <option value="9">G{unit}</option>
                    <option value="12">T{unit}</option>
                </select>
            </div>
        """.format(
            id=self.id,
            disabled="disabled" if self.disabled else "",
            unit=self.unit,
        )

        return """
            <div class="input-group input-group-sm exponential-input">
                {input}
                {append}
                {errors}
            </div>
        """.format(
            input=self.render_input(value, errors),
            append=append,
            errors=self.render_errors(errors)
        )

    def parse(self, data):
        exponent_id = "{}-exponent".format(self.id)
        if self.id in data and exponent_id in data:
            value = int(float(data[self.id][0]) * 10 ** int(data[exponent_id][0]))
            return {self.id: value}
        return {}
