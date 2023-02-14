from pycsdr.types import Format
from csdr.module import PopenModule


class Msk144Module(PopenModule):
    def getCommand(self):
        return ["msk144decoder"]

    def getInputFormat(self) -> Format:
        return Format.SHORT

    def getOutputFormat(self) -> Format:
        return Format.CHAR
