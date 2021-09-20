from csdr.chain.demodulator import BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain
from csdr.module.m17 import M17Module
from pycsdr.modules import FmDemod, Limit, Convert
from pycsdr.types import Format
from digiham.modules import DcBlock


class M17(BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain):
    def __init__(self):
        workers = [
            FmDemod(),
            DcBlock(),
            Limit(),
            Convert(Format.FLOAT, Format.SHORT),
            M17Module(),
        ]
        super().__init__(workers)

    def getFixedIfSampleRate(self) -> int:
        return 48000

    def getFixedAudioRate(self) -> int:
        return 8000

    def supportsSquelch(self) -> bool:
        return False
