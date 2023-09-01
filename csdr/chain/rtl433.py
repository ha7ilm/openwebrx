from owrx.ism.rtl433 import Rtl433Module, JsonParser
from csdr.chain.demodulator import ServiceDemodulator


class Rtl433(ServiceDemodulator):
    def getFixedAudioRate(self) -> int:
        return 250000

    def __init__(self):
        super().__init__(
            [
                Rtl433Module(),
                JsonParser(),
            ]
        )
