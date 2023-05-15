from owrx.form.input import TextAreaInput
from owrx.form.input.converter import Converter


class ReceiverKeysConverter(Converter):
    def convert_to_form(self, value):
        return "" if value is None else "\n".join(value)

    def convert_from_form(self, value):
        # \r\n or \n? this should work with both.
        stripped = [v.strip("\r ") for v in value.split("\n")]
        # omit empty lines
        return [v for v in stripped if v]


class ReceiverKeysInput(TextAreaInput):
    def __init__(self, id, label):
        super().__init__(
            id,
            label,
            infotext="Put the keys you receive on listing sites (e.g. "
            + '<a href="https://www.receiverbook.de" target="_blank">Receiverbook</a>) here, one per line',
        )

    def input_properties(self, value, errors):
        props = super().input_properties(value, errors)
        # disable word wrap on the textarea.
        # why? keys are longer than the input, and word wrap makes the "one per line" instruction confusing.
        props["wrap"] = "off"
        return props

    def defaultConverter(self):
        return ReceiverKeysConverter()
