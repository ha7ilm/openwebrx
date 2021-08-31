from csdr.chain.demodulator import SecondaryDemodulator, FixedAudioRateChain
from owrx.audio.chopper import AudioChopper
from pycsdr.modules import Agc, Convert
from pycsdr.types import Format


class AudioChopperDemodulator(SecondaryDemodulator, FixedAudioRateChain):
    # TODO parser typing
    def __init__(self, mode: str, parser):
        workers = [Convert(Format.FLOAT, Format.SHORT), AudioChopper(mode, parser)]
        super().__init__(workers)

    def getFixedAudioRate(self):
        return 12000
