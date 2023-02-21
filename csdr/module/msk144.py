from pycsdr.types import Format
from csdr.module import PopenModule, ThreadModule
from owrx.wsjt import WsjtParser, Msk144Profile
import pickle

import logging
logger = logging.getLogger(__name__)


class Msk144Module(PopenModule):
    def getCommand(self):
        return ["msk144decoder"]

    def getInputFormat(self) -> Format:
        return Format.SHORT

    def getOutputFormat(self) -> Format:
        return Format.CHAR


class ParserAdapter(ThreadModule):
    def __init__(self):
        self.retained = bytes()
        self.parser = WsjtParser()
        self.dialFrequency = 0
        super().__init__()

    def run(self):
        profile = Msk144Profile()

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

                # parse all completed lines
                for line in lines[0:-1]:
                    # actual messages from msk144decoder should start with "*** "
                    if line[0:4] == b"*** ":
                        self.writer.write(pickle.dumps(self.parser.parse(profile, self.dialFrequency, line[4:])))

    def getInputFormat(self) -> Format:
        return Format.CHAR

    def getOutputFormat(self) -> Format:
        return Format.CHAR

    def setDialFrequency(self, frequency: int) -> None:
        self.dialFrequency = frequency
