from owrx.ism.rtl433 import Rtl433Module, IsmParser
from csdr.chain.demodulator import ServiceDemodulator


class Rtl433(ServiceDemodulator):
    def getFixedAudioRate(self) -> int:
        return 1200000

    def __init__(self):
        super().__init__(
            [
                Rtl433Module(),
                IsmParser(),
            ]
        )

    def supportsSquelch(self) -> bool:
        return False
