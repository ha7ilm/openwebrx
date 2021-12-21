from csdr.module import PopenModule
from pycsdr.types import Format
from pycsdr.modules import Writer
from subprocess import Popen, PIPE
from threading import Thread

import re
import pickle


class M17Module(PopenModule):
    lsfRegex = re.compile("SRC: ([a-zA-Z0-9]+), DEST: ([a-zA-Z0-9]+)")

    def __init__(self):
        super().__init__()
        self.metawriter = None

    def getInputFormat(self) -> Format:
        return Format.SHORT

    def getOutputFormat(self) -> Format:
        return Format.SHORT

    def getCommand(self):
        return ["m17-demod", "-l"]

    def _getProcess(self):
        return Popen(self.getCommand(), stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def start(self):
        super().start()
        Thread(target=self._readOutput).start()

    def _readOutput(self):
        while True:
            line = self.process.stderr.readline()
            if not line:
                break
            self.parseOutput(line.decode())

    def parseOutput(self, line):
        if self.metawriter is None:
            return
        matches = self.lsfRegex.match(line)
        msg = {"protocol": "M17"}
        if matches:
            # fake sync
            msg["sync"] = "voice"
            msg["source"] = matches.group(1)
            msg["destination"] = matches.group(2)
        elif line.startswith("EOS"):
            pass
        else:
            return
        self.metawriter.write(pickle.dumps(msg))

    def setMetaWriter(self, writer: Writer) -> None:
        self.metawriter = writer
