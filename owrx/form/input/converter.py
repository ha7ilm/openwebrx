from abc import ABC, abstractmethod
from owrx.jsons import Encoder
import json


class Converter(ABC):
    @abstractmethod
    def convert_to_form(self, value):
        pass

    @abstractmethod
    def convert_from_form(self, value):
        pass


class NullConverter(Converter):
    """
    The default converter class
    Does not change the value in any way, just passes them through
    """
    def convert_to_form(self, value):
        return value

    def convert_from_form(self, value):
        return value


class TextConverter(Converter):
    """
    Converter class for text inputs
    Does nothing more than to prevent the special python value "None" from appearing in the form
    The string "None" should pass
    """
    def convert_to_form(self, value):
        if value is None:
            return ""
        return value

    def convert_from_form(self, value):
        return value


class OptionalConverter(Converter):
    """
    Transforms a special form value to None
    The default is to look for an empty string, but this can be used to adopt to other types.
    If the default is not found, the actual value is passed to the sub_converter for further transformation.
    useful for optional fields since None is not stored in the configuration
    """

    def __init__(self, sub_converter: Converter = None, defaultFormValue=""):
        self.sub_converter = NullConverter() if sub_converter is None else sub_converter
        self.defaultFormValue = defaultFormValue

    def convert_to_form(self, value):
        return self.defaultFormValue if value is None else self.sub_converter.convert_to_form(value)

    def convert_from_form(self, value):
        return None if value == self.defaultFormValue else self.sub_converter.convert_from_form(value)


class IntConverter(Converter):
    def convert_to_form(self, value):
        return str(value)

    def convert_from_form(self, value):
        return int(value)


class FloatConverter(Converter):
    def convert_to_form(self, value):
        return str(value)

    def convert_from_form(self, value):
        return float(value)


class EnumConverter(Converter):
    def __init__(self, enumCls):
        self.enumCls = enumCls

    def convert_to_form(self, value):
        if value is None:
            return None
        try:
            return self.enumCls(value).name
        # if the current value is not part of the enum, this will happen:
        except ValueError:
            # and this will restore the default
            return None

    def convert_from_form(self, value):
        return self.enumCls[value].value


class JsonConverter(Converter):
    def convert_to_form(self, value):
        return json.dumps(value, cls=Encoder)

    def convert_from_form(self, value):
        return json.loads(value)


class WaterfallColorsConverter(Converter):
    def convert_to_form(self, value):
        if value is None:
            return ""
        return "\n".join("#{:06x}".format(v) for v in value)

    def convert_from_form(self, value):
        def parseString(s):
            try:
                if s.startswith("#"):
                    return int(s[1:], 16)
                # int() with base 0 can accept "0x" prefixed hex strings, or int numbers
                return int(s, 0)
            except ValueError:
                return None

        # \r\n or \n? this should work with both.
        values = [parseString(v.strip("\r ")) for v in value.split("\n")]
        return [v for v in values if v is not None]
