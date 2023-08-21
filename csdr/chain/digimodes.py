from csdr.chain.demodulator import ServiceDemodulator, SecondaryDemodulator, DialFrequencyReceiver, SecondarySelectorChain
from csdr.module.msk144 import Msk144Module, ParserAdapter
from owrx.audio.chopper import AudioChopper, AudioChopperParser
from owrx.aprs.kiss import KissDeframer
from owrx.aprs import Ax25Parser, AprsParser
from pycsdr.modules import Convert, FmDemod, Agc, TimingRecovery, DBPskDecoder, VaricodeDecoder, RttyDecoder, BaudotDecoder, Lowpass
from pycsdr.types import Format
from owrx.aprs.direwolf import DirewolfModule


class AudioChopperDemodulator(ServiceDemodulator, DialFrequencyReceiver):
    def __init__(self, mode: str, parser: AudioChopperParser):
        self.chopper = AudioChopper(mode, parser)
        workers = [Convert(Format.FLOAT, Format.SHORT), self.chopper]
        super().__init__(workers)

    def getFixedAudioRate(self):
        return 12000

    def setDialFrequency(self, frequency: int) -> None:
        self.chopper.setDialFrequency(frequency)


class Msk144Demodulator(ServiceDemodulator, DialFrequencyReceiver):
    def __init__(self):
        self.parser = ParserAdapter()
        workers = [
            Convert(Format.FLOAT, Format.SHORT),
            Msk144Module(),
            self.parser,
        ]
        super().__init__(workers)

    def getFixedAudioRate(self) -> int:
        return 12000

    def setDialFrequency(self, frequency: int) -> None:
        self.parser.setDialFrequency(frequency)


class PacketDemodulator(ServiceDemodulator, DialFrequencyReceiver):
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


class PskDemodulator(SecondaryDemodulator, SecondarySelectorChain):
    def __init__(self, baudRate: float):
        self.baudRate = baudRate
        # this is an assumption, we will adjust in setSampleRate
        self.sampleRate = 12000
        secondary_samples_per_bits = int(round(self.sampleRate / self.baudRate)) & ~3
        workers = [
            Agc(Format.COMPLEX_FLOAT),
            TimingRecovery(Format.COMPLEX_FLOAT, secondary_samples_per_bits, 0.5, 2),
            DBPskDecoder(),
            VaricodeDecoder(),
        ]
        super().__init__(workers)

    def getBandwidth(self):
        return self.baudRate

    def setSampleRate(self, sampleRate: int) -> None:
        if sampleRate == self.sampleRate:
            return
        self.sampleRate = sampleRate
        secondary_samples_per_bits = int(round(self.sampleRate / self.baudRate)) & ~3
        self.replace(1, TimingRecovery(Format.COMPLEX_FLOAT, secondary_samples_per_bits, 0.5, 2))


class RttyDemodulator(SecondaryDemodulator, SecondarySelectorChain):
    def __init__(self, baudRate, bandWidth, invert=False):
        self.baudRate = baudRate
        self.bandWidth = bandWidth
        self.invert = invert
        # this is an assumption, we will adjust in setSampleRate
        self.sampleRate = 12000
        secondary_samples_per_bit = int(round(self.sampleRate / self.baudRate))
        cutoff = self.baudRate / self.sampleRate
        loop_gain = self.sampleRate / self.getBandwidth() / 5
        workers = [
            Agc(Format.COMPLEX_FLOAT),
            FmDemod(),
            Lowpass(Format.FLOAT, cutoff),
            TimingRecovery(Format.FLOAT, secondary_samples_per_bit, loop_gain, 10),
            RttyDecoder(invert),
            BaudotDecoder(),
        ]
        super().__init__(workers)

    def getBandwidth(self) -> float:
        return self.bandWidth

    def setSampleRate(self, sampleRate: int) -> None:
        if sampleRate == self.sampleRate:
            return
        self.sampleRate = sampleRate
        secondary_samples_per_bit = int(round(self.sampleRate / self.baudRate))
        cutoff = self.baudRate / self.sampleRate
        loop_gain = self.sampleRate / self.getBandwidth() / 5
        self.replace(2, Lowpass(Format.FLOAT, cutoff))
        self.replace(3, TimingRecovery(Format.FLOAT, secondary_samples_per_bit, loop_gain, 10))
