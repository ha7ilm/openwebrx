from pycsdr.modules import Module as BaseModule
from pycsdr.modules import Reader, Writer
from pycsdr.types import Format
from abc import ABCMeta, abstractmethod
from threading import Thread
from io import BytesIO
import pickle


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


class ThreadModule(Module, Thread, metaclass=ABCMeta):
    def __init__(self):
        self.doRun = True
        super().__init__()
        Thread.__init__(self)

    def _checkStart(self) -> None:
        if self.reader is not None and self.writer is not None:
            self.start()

    def setReader(self, reader: Reader) -> None:
        super().setReader(reader)
        self._checkStart()

    def setWriter(self, writer: Writer) -> None:
        super().setWriter(writer)
        self._checkStart()

    @abstractmethod
    def run(self):
        pass

    def stop(self):
        self.doRun = False
        self.reader.stop()


class PickleModule(ThreadModule):
    def getInputFormat(self) -> Format:
        return Format.CHAR

    def getOutputFormat(self) -> Format:
        return Format.CHAR

    def run(self):
        while self.doRun:
            data = self.reader.read()
            if data is None:
                self.doRun = False
                break
            io = BytesIO(data.tobytes())
            try:
                while True:
                    output = self.process(pickle.load(io))
                    if output is not None:
                        self.writer.write(pickle.dumps(output))
            except EOFError:
                pass

    @abstractmethod
    def process(self, input):
        pass
