from csdr.chain.demodulator import BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain
from pycsdr.modules import Convert, Downmix
from pycsdr.types import Format
from csdr.module.drm import DrmModule


class Drm(BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain):
    def __init__(self):
        workers = [
            Convert(Format.COMPLEX_FLOAT, Format.COMPLEX_SHORT),
            DrmModule(),
            Downmix(Format.SHORT),
        ]
        super().__init__(workers)

    def supportsSquelch(self) -> bool:
        return False

    def getFixedIfSampleRate(self) -> int:
        return 48000

    def getFixedAudioRate(self) -> int:
        return 48000
