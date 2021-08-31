from csdr.chain.demodulator import SecondaryDemodulator, FixedAudioRateChain, DialFrequencyReceiver
from owrx.audio.chopper import AudioChopper
from pycsdr.modules import Agc, Convert
from pycsdr.types import Format


class AudioChopperDemodulator(SecondaryDemodulator, FixedAudioRateChain, DialFrequencyReceiver):
    # TODO parser typing
    def __init__(self, mode: str, parser):
        self.chopper = AudioChopper(mode, parser)
        workers = [Convert(Format.FLOAT, Format.SHORT), self.chopper]
        super().__init__(workers)

    def getFixedAudioRate(self):
        return 12000

    def setDialFrequency(self, frequency: int) -> None:
        self.chopper.setDialFrequency(frequency)
