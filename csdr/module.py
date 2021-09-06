from pycsdr.modules import Module as BaseModule
from pycsdr.modules import Reader, Writer
from pycsdr.types import Format
from abc import ABCMeta, abstractmethod


class Module(BaseModule, metaclass=ABCMeta):
    def __init__(self):
        self.reader = None
        self.writer = None
        super().__init__()

    def setReader(self, reader: Reader) -> None:
        self.reader = reader

    def setWriter(self, writer: Writer) -> None:
        self.writer = writer

    @abstractmethod
    def getInputFormat(self) -> Format:
        pass

    @abstractmethod
    def getOutputFormat(self) -> Format:
        pass
