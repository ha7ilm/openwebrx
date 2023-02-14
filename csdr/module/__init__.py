from pycsdr.modules import Module as BaseModule
from pycsdr.modules import Reader, Writer
from pycsdr.types import Format
from abc import ABCMeta, abstractmethod
from threading import Thread
from io import BytesIO
from subprocess import Popen, PIPE
from functools import partial
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

    def pump(self, read, write):
        def copy():
            while True:
                data = None
                try:
                    data = read()
                except ValueError:
                    pass
                except BrokenPipeError:
                    break
                if data is None or isinstance(data, bytes) and len(data) == 0:
                    break
                write(data)

        return copy


class AutoStartModule(Module, metaclass=ABCMeta):
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
    def start(self):
        pass


class ThreadModule(AutoStartModule, Thread, metaclass=ABCMeta):
    def __init__(self):
        self.doRun = True
        super().__init__()
        Thread.__init__(self)

    @abstractmethod
    def run(self):
        pass

    def stop(self):
        self.doRun = False
        self.reader.stop()

    def start(self):
        Thread.start(self)


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


class PopenModule(AutoStartModule, metaclass=ABCMeta):
    def __init__(self):
        self.process = None
        super().__init__()

    @abstractmethod
    def getCommand(self):
        pass

    def _getProcess(self):
        return Popen(self.getCommand(), stdin=PIPE, stdout=PIPE)

    def start(self):
        self.process = self._getProcess()
        # resume in case the reader has been stop()ed before
        self.reader.resume()
        Thread(target=self.pump(self.reader.read, self.process.stdin.write)).start()
        Thread(target=self.pump(partial(self.process.stdout.read1, 1024), self.writer.write)).start()

    def stop(self):
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
            self.process = None
        self.reader.stop()
