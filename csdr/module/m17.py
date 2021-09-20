from csdr.module import PopenModule
from pycsdr.types import Format


class M17Module(PopenModule):
    def getInputFormat(self) -> Format:
        return Format.SHORT

    def getOutputFormat(self) -> Format:
        return Format.SHORT

    def getCommand(self):
        return ["m17-demod"]
