from abc import ABC, abstractmethod


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


