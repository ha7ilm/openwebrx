from csdr.chain.demodulator import BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain, HdAudio
from csdreti.modules import EtiDecoder
from owrx.dab.dablin import DablinModule
from pycsdr.modules import Downmix
from pycsdr.types import Format


class Dablin(BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain, HdAudio):
    def __init__(self):
        workers = [
            EtiDecoder(),
            DablinModule(),
            Downmix(Format.FLOAT),
        ]
        super().__init__(workers)

    def getFixedIfSampleRate(self) -> int:
        return 2048000

    def getFixedAudioRate(self) -> int:
        return 48000
