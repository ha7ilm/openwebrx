from csdr.chain.demodulator import ServiceDemodulator
from csdr.module import JsonParser
from owrx.vdl2.dumpvdl2 import DumpVDL2Module
from pycsdr.modules import Convert
from pycsdr.types import Format


class DumpVDL2(ServiceDemodulator):
    def __init__(self):
        super().__init__([
            Convert(Format.COMPLEX_FLOAT, Format.COMPLEX_SHORT),
            DumpVDL2Module(),
            JsonParser("VDL2")
        ])

    def getFixedAudioRate(self) -> int:
        return 105000
