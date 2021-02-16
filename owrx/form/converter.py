from abc import ABC, abstractmethod
import json


class Converter(ABC):
    @abstractmethod
    def convert_to_form(self, value):
        pass

    @abstractmethod
    def convert_from_form(self, value):
        pass


class NullConverter(Converter):
    def convert_to_form(self, value):
        return value

    def convert_from_form(self, value):
        return value


class OptionalConverter(Converter):
    """
    Maps None to an empty string, and reverse
    useful for optional fields
    """

    def convert_to_form(self, value):
        return "" if value is None else value

    def convert_from_form(self, value):
        return value if value else None


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
        return None if value is None else self.enumCls(value).name

    def convert_from_form(self, value):
        return self.enumCls[value].value


class JsonConverter(Converter):
    def convert_to_form(self, value):
        return json.dumps(value)

    def convert_from_form(self, value):
        return json.loads(value)


class WaterfallColorsConverter(Converter):
    def convert_to_form(self, value):
        if value is None:
            return ""
        return "\n".join("#{:06x}".format(v) for v in value)

    def convert_from_form(self, value):
        def parseString(s):
            if s.startswith("#"):
                return int(s[1:], 16)
            # int() with base 0 can accept "0x" prefixed hex strings, or int numbers
            return int(s, 0)

        # \r\n or \n? this should work with both.
        return [parseString(v.strip("\r ")) for v in value.split("\n")]
