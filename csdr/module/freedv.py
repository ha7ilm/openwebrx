from pycsdr.types import Format
from csdr.module import PopenModule


class FreeDVModule(PopenModule):
    def getInputFormat(self) -> Format:
        return Format.SHORT

    def getOutputFormat(self) -> Format:
        return Format.SHORT

    def getCommand(self):
        return ["freedv_rx", "1600", "-", "-"]
