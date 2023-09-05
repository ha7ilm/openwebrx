from csdr.chain.demodulator import ServiceDemodulator
from owrx.hfdl.dumphfdl import DumpHFDLModule, HFDLMessageParser


class DumpHFDL(ServiceDemodulator):
    def __init__(self):
        super().__init__([
            DumpHFDLModule(),
            HFDLMessageParser(),
        ])

    def getFixedAudioRate(self) -> int:
        return 12000
