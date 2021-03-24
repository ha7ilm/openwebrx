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
