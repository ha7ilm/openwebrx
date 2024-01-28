from csdr.module import JsonParser
from owrx.ism.rtl433 import Rtl433Module
from csdr.chain.demodulator import ServiceDemodulator


class Rtl433(ServiceDemodulator):
    def getFixedAudioRate(self) -> int:
        return 1200000

    def __init__(self):
        super().__init__(
            [
                Rtl433Module(),
                JsonParser("ISM"),
            ]
        )

    def supportsSquelch(self) -> bool:
        return False
