from abc import ABC, abstractmethod


class ValidatorException(Exception):
    pass


class Validator(ABC):
    @staticmethod
    def of(x):
        if isinstance(x, Validator):
            return x
        if callable(x):
            return LambdaValidator(x)
        raise ValidatorException("Cannot create validator")

    @abstractmethod
    def isValid(self, value):
        pass


class LambdaValidator(Validator):
    def __init__(self, c):
        self.callable = c

    def isValid(self, value):
        return self.callable(value)


class NumberValidator(Validator):
    def isValid(self, value):
        return isinstance(value, int) or isinstance(value, float)


class IntegerValidator(Validator):
    def isValid(self, value):
        return isinstance(value, int)


class StringValidator(Validator):
    def isValid(self, value):
        return isinstance(value, str)
