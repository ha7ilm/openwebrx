from owrx.form.input.converter import Converter


class ReceiverKeysConverter(Converter):
    def convert_to_form(self, value):
        return "" if value is None else "\n".join(value)

    def convert_from_form(self, value):
        # \r\n or \n? this should work with both.
        return [v.strip("\r ") for v in value.split("\n")]
