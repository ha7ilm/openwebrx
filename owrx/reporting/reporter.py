from abc import ABC, abstractmethod


class Reporter(ABC):
    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def spot(self, spot):
        pass


class FilteredReporter(Reporter):
    @abstractmethod
    def getSupportedModes(self):
        return []
