from csdr.chain.demodulator import SecondaryDemodulator, FixedAudioRateChain, DialFrequencyReceiver
from owrx.audio.chopper import AudioChopper
from owrx.aprs.kiss import KissDeframer
from owrx.aprs import Ax25Parser, AprsParser
from pycsdr.modules import Convert, FmDemod
from pycsdr.types import Format
from owrx.aprs.module import DirewolfModule


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


class PacketDemodulator(SecondaryDemodulator, FixedAudioRateChain, DialFrequencyReceiver):
    def __init__(self, service: bool = False):
        self.parser = AprsParser()
        workers = [
            FmDemod(),
            Convert(Format.FLOAT, Format.SHORT),
            DirewolfModule(service=service),
            KissDeframer(),
            Ax25Parser(),
            self.parser,
        ]
        super().__init__(workers)

    def supportsSquelch(self) -> bool:
        return False

    def getFixedAudioRate(self) -> int:
        return 48000

    def setDialFrequency(self, frequency: int) -> None:
        self.parser.setDialFrequency(frequency)
