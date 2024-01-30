from abc import ABC, abstractmethod
from owrx.form.error import ValidationError
from typing import List


class Validator(ABC):
    @abstractmethod
    def validate(self, key, value) -> None:
        pass


class RequiredValidator(Validator):
    def validate(self, key, value) -> None:
        if value is None or value == "":
            raise ValidationError(key, "Field is required")


class Range(object):
    def __init__(self, start: int, end: int = None):
        self.start = start
        self.end = end if end is not None else start

    def isInRange(self, value):
        return self.start <= value <= self.end

    def __str__(self):
        if self.start == self.end:
            return str(self.start)
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
    def __init__(self, rangeList: List[Range]):
        self.rangeList = rangeList

    def validate(self, key, value) -> None:
        if not any(range for range in self.rangeList if range.isInRange(value)):
            raise ValidationError(
                key, "Value is outside of the allowed range(s) {}".format(self._rangeStr())
            )

    def _rangeStr(self):
        return "[{}]".format(", ".join(str(r) for r in self.rangeList))


class AddressAndOptionalPortValidator(Validator):
    def validate(self, key, value) -> None:
        parts = value.split(":")
        if len(parts) > 2:
            raise ValidationError(key, "Value contains too many colons")

        if len(parts) > 1:
            try:
                port = int(parts[1])
            except ValueError:
                raise ValidationError(key, "Port number must be numeric")
            if not 0 <= port <= 65535:
                raise ValidationError(key, "Port number out of range")
