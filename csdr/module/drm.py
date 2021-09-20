from csdr.module import PopenModule
from pycsdr.types import Format


class DrmModule(PopenModule):
    def getInputFormat(self) -> Format:
        return Format.COMPLEX_FLOAT

    def getOutputFormat(self) -> Format:
        return Format.SHORT

    def getCommand(self):
        # dream -c 6 --sigsrate 48000 --audsrate 48000 -I - -O -
        return ["dream", "-c", "6", "--sigsrate", "48000", "--audsrate", "48000", "-I", "-", "-O", "-"]
