from abc import ABC, abstractmethod
from owrx.form.error import ValidationError


class Validator(ABC):
    @abstractmethod
    def validate(self, key, value):
        pass


class RequiredValidator(Validator):
    def validate(self, key, value):
        if value is None or value == "":
            raise ValidationError(key, "Field is required")

class RangeValidator(Validator):
    def __init__(self, minValue, maxValue):
        self.minValue = minValue
        self.maxValue = maxValue

    def validate(self, key, value):
        if value is None or value == "":
            return # Ignore empty values
        n = float(value)
        if n < self.minValue or n > self.maxValue:
            raise ValidationError(key, 'Value must be between %s and %s'%(self.minValue, self.maxValue))
