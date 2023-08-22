from pycsdr.modules import Convert
from pycsdr.types import Format
from csdr.chain.demodulator import ServiceDemodulator
from owrx.adsb.dump1090 import Dump1090Module, RawDeframer, ModeSParser


class Dump1090(ServiceDemodulator):
    def __init__(self):
        workers = [
            Convert(Format.COMPLEX_FLOAT, Format.COMPLEX_SHORT),
            Dump1090Module(),
            RawDeframer(),
            ModeSParser(),
        ]

        super().__init__(workers)
    pass

    def getFixedAudioRate(self) -> int:
        return 2400000
