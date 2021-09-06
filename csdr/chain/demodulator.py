from csdr.chain import Chain
from abc import ABC, abstractmethod


class BaseDemodulatorChain(Chain):
    def supportsSquelch(self) -> bool:
        return True

    def setSampleRate(self, sampleRate: int) -> None:
        pass


class SecondaryDemodulator(Chain):
    def supportsSquelch(self) -> bool:
        return True


class FixedAudioRateChain(ABC):
    @abstractmethod
    def getFixedAudioRate(self) -> int:
        pass


class FixedIfSampleRateChain(ABC):
    @abstractmethod
    def getFixedIfSampleRate(self) -> int:
        pass


class DialFrequencyReceiver(ABC):
    @abstractmethod
    def setDialFrequency(self, frequency: int) -> None:
        pass


# marker interface
class HdAudio:
    pass
