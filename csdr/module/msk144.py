from pycsdr.types import Format
from pycsdr.modules import ExecModule
from csdr.module import LineBasedModule
from owrx.wsjt import WsjtParser, Msk144Profile
import pickle

import logging
logger = logging.getLogger(__name__)


class Msk144Module(ExecModule):
    def __init__(self):
        super().__init__(
            Format.SHORT,
            Format.CHAR,
            ["msk144decoder"]
        )


class ParserAdapter(LineBasedModule):
    def __init__(self):
        self.parser = WsjtParser()
        self.dialFrequency = 0
        self.profile = Msk144Profile()
        super().__init__()

    def process(self, line: bytes):
        # actual messages from msk144decoder should start with "*** "
        if line[0:4] == b"*** ":
            return self.parser.parse(self.profile, self.dialFrequency, line[4:])

    def setDialFrequency(self, frequency: int) -> None:
        self.dialFrequency = frequency
