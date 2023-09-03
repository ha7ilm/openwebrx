from csdr.chain.demodulator import ServiceDemodulator
from owrx.hfdl.dumphfdl import DumpHFDLModule
from csdr.module import JsonParser


class DumpHFDL(ServiceDemodulator):
    def __init__(self):
        super().__init__([
            DumpHFDLModule(),
            JsonParser("HFDL"),
        ])

    def getFixedAudioRate(self) -> int:
        return 12000
