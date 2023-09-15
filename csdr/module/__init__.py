from pycsdr.modules import Module as BaseModule
from pycsdr.modules import Reader, Writer, Buffer
from pycsdr.types import Format
from abc import ABCMeta, abstractmethod
from threading import Thread
from io import BytesIO
from subprocess import Popen, PIPE, TimeoutExpired
from functools import partial
import pickle
import logging
import json

logger = logging.getLogger(__name__)


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
                try:
                    write(data)
                except BrokenPipeError:
                    break

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


class LineBasedModule(ThreadModule, metaclass=ABCMeta):
    def __init__(self):
        self.retained = bytes()
        super().__init__()

    def getInputFormat(self) -> Format:
        return Format.CHAR

    def getOutputFormat(self) -> Format:
        return Format.CHAR

    def run(self):
        while self.doRun:
            data = self.reader.read()
            if data is None:
                self.doRun = False
            else:
                self.retained += data
                lines = self.retained.split(b"\n")

                # keep the last line
                # this should either be empty if the last char was \n
                # or an incomplete line if the read returned early
                self.retained = lines[-1]

                # log all completed lines
                for line in lines[0:-1]:
                    parsed = self.process(line)
                    if parsed is not None:
                        self.writer.write(pickle.dumps(parsed))

    @abstractmethod
    def process(self, line: bytes) -> any:
        pass


class JsonParser(LineBasedModule):
    def __init__(self, mode: str):
        self.mode = mode
        super().__init__()

    def process(self, line):
        try:
            msg = json.loads(line)
            msg["mode"] = self.mode
            logger.debug(msg)
            return msg
        except json.JSONDecodeError:
            logger.exception("error parsing rtl433 json")


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
            # Try terminating normally, kill if failed to terminate
            try:
                self.process.terminate()
                self.process.wait(3)
            except TimeoutExpired:
                self.process.kill()
            self.process = None
        self.reader.stop()


class LogReader(Thread):
    def __init__(self, prefix: str, buffer: Buffer):
        self.reader = buffer.getReader()
        self.logger = logging.getLogger(prefix)
        self.retained = bytes()
        super().__init__()
        self.start()

    def run(self) -> None:
        while True:
            data = self.reader.read()
            if data is None:
                return

            self.retained += data
            lines = self.retained.split(b"\n")

            # keep the last line
            # this should either be empty if the last char was \n
            # or an incomplete line if the read returned early
            self.retained = lines[-1]

            # log all completed lines
            for line in lines[0:-1]:
                self.logger.info("{}: {}".format("STDOUT", line.strip(b'\n').decode()))

    def stop(self):
        self.reader.stop()
