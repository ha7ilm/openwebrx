from abc import ABC, abstractmethod


class Filter(ABC):
    @abstractmethod
    def apply(self, prop) -> bool:
        pass


class ByPropertyName(Filter):
    def __init__(self, *props):
        self.props = props

    def apply(self, prop) -> bool:
        return prop in self.props


class ByLambda(Filter):
    def __init__(self, func):
        self.func = func

    def apply(self, prop) -> bool:
        return self.func(prop)
