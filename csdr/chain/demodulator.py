from csdr.chain import Chain
from abc import ABC, abstractmethod


class BaseDemodulatorChain(Chain):
    def getFixedIfSampleRate(self):
        return None

    def supportsSquelch(self):
        return True


class FixedAudioRateChain(ABC):
    @abstractmethod
    def getFixedAudioRate(self):
        pass


class FixedIfSampleRateChain(ABC):
    @abstractmethod
    def getFixedIfSampleRate(self):
        return self.fixedIfSampleRate


# marker interface
class HdAudio:
    pass
