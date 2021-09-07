from csdr.chain.demodulator import BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain
from pycsdr.modules import Convert
from pycsdr.types import Format
from owrx.drm import DrmModule


class Drm(BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain):
    def __init__(self):
        workers = [Convert(Format.COMPLEX_FLOAT, Format.COMPLEX_SHORT), DrmModule()]
        super().__init__(workers)

    def getFixedIfSampleRate(self) -> int:
        return 48000

    def getFixedAudioRate(self) -> int:
        return 48000
