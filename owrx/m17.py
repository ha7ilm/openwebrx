from csdr.module import AutoStartModule
from pycsdr.types import Format
from subprocess import Popen, PIPE
import threading


class M17Module(AutoStartModule):
    def __init__(self):
        self.process = None
        super().__init__()

    def getInputFormat(self) -> Format:
        return Format.SHORT

    def getOutputFormat(self) -> Format:
        return Format.SHORT

    def start(self):
        self.process = Popen(["m17-demod"], stdin=PIPE, stdout=PIPE)
        threading.Thread(target=self.pump(self.reader.read, self.process.stdin.write)).start()
        threading.Thread(target=self.pump(self.process.stdout.read, self.writer.write)).start()

    def stop(self):
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
            self.process = None
        self.reader.stop()

    def pump(self, read, write):
        def copy():
            while True:
                data = None
                try:
                    data = read()
                except ValueError:
                    pass
                if data is None or isinstance(data, bytes) and len(data) == 0:
                    break
                write(data)

        return copy
