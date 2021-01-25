from abc import ABC, abstractmethod
from functools import reduce
from operator import or_


class ValidatorException(Exception):
    pass


class Validator(ABC):
    @staticmethod
    def of(x):
        if isinstance(x, Validator):
            return x
        if callable(x):
            return LambdaValidator(x)
        if x in validator_types:
            return validator_types[x]()
        raise ValidatorException("Cannot create validator")

    @abstractmethod
    def isValid(self, value):
        pass


class LambdaValidator(Validator):
    def __init__(self, c):
        self.callable = c

    def isValid(self, value):
        return self.callable(value)


class TypeValidator(Validator):
    def __init__(self, type):
        self.type = type
        super().__init__()

    def isValid(self, value):
        return isinstance(value, self.type)


class IntegerValidator(TypeValidator):
    def __init__(self):
        super().__init__(int)


class FloatValidator(TypeValidator):
    def __init__(self):
        super().__init__(float)


class StringValidator(TypeValidator):
    def __init__(self):
        super().__init__(str)


class BoolValidator(TypeValidator):
    def __init__(self):
        super().__init__(bool)


class OrValidator(Validator):
    def __init__(self, *validators):
        self.validators = validators
        super().__init__()

    def isValid(self, value):
        return reduce(
            or_,
            [v.isValid(value) for v in self.validators],
            False
        )


class NumberValidator(OrValidator):
    def __init__(self):
        super().__init__(IntegerValidator(), FloatValidator())


class RegexValidator(StringValidator):
    def __init__(self, regex):
        self.regex = regex
        super().__init__()

    def isValid(self, value):
        return super().isValid(value) and self.regex.match(value) is not None


validator_types = {
    "string": StringValidator,
    "str": StringValidator,
    "integer": IntegerValidator,
    "int": IntegerValidator,
    "number": NumberValidator,
    "num": NumberValidator,
}
