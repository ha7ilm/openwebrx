from csdr.chain.demodulator import BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain
from csdr.module.freedv import FreeDVModule
from pycsdr.modules import RealPart, Agc, Convert
from pycsdr.types import Format


class FreeDV(BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain):
    def __init__(self):
        agc = Agc(Format.SHORT)
        agc.setMaxGain(30)
        agc.setInitialGain(3)
        workers = [
            RealPart(),
            Agc(Format.FLOAT),
            Convert(Format.FLOAT, Format.SHORT),
            FreeDVModule(),
            agc,
        ]
        super().__init__(workers)

    def getFixedIfSampleRate(self) -> int:
        return 8000

    def getFixedAudioRate(self) -> int:
        return 8000

    def supportsSquelch(self) -> bool:
        return False
