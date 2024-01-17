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


class Range(object):
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

    def isInRange(self, value):
        return self.start <= value <= self.end

    def __str__(self):
        return "{start}...{end}".format(**vars(self))


class RangeValidator(Validator):
    def __init__(self, minValue, maxValue):
        self.range = Range(minValue, maxValue)

    def validate(self, key, value) -> None:
        if value is None or value == "":
            return  # Ignore empty values
        if not self.range.isInRange(float(value)):
            raise ValidationError(
                key, "Value must be between {min} and {max}".format(min=self.range.start, max=self.range.end)
            )


class RangeListValidator(Validator):
    def __init__(self, rangeList: list[Range]):
        self.rangeList = rangeList

    def validate(self, key, value) -> None:
        if not any(range for range in self.rangeList if range.isInRange(value)):
            raise ValidationError(
                key, "Value is out of range {}".format(self._rangeStr())
            )

    def _rangeStr(self):
        return "[{}]".format(", ".join(str(r) for r in self.rangeList))
