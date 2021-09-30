from abc import ABC, abstractmethod
from owrx.form.error import ValidationError


class Validator(ABC):
    @abstractmethod
    def validate(self, key, value) -> None:
        pass


class RequiredValidator(Validator):
    def validate(self, key, value) -> None:
        if value is None or value == "":
            raise ValidationError(key, "Field is required")


class RangeValidator(Validator):
    def __init__(self, minValue, maxValue):
        self.minValue = minValue
        self.maxValue = maxValue

    def validate(self, key, value) -> None:
        if value is None or value == "":
            return  # Ignore empty values
        n = float(value)
        if n < self.minValue or n > self.maxValue:
            raise ValidationError(
                key, "Value must be between {min} and {max}".format(min=self.minValue, max=self.maxValue)
            )
