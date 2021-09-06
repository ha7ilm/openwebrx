from csdr.chain import Chain
from csdr.chain.selector import Selector
from csdr.chain.demodulator import BaseDemodulatorChain, SecondaryDemodulator, FixedAudioRateChain
from pycsdr.types import Format


class ServiceDemodulatorChain(Chain):
    def __init__(self, demod: BaseDemodulatorChain, secondaryDemod: SecondaryDemodulator, sampleRate: int, shiftRate: float):
        # TODO magic number... check if this edge case even exsists and change the api if possible
        rate = secondaryDemod.getFixedAudioRate() if isinstance(secondaryDemod, FixedAudioRateChain) else 1200

        self.selector = Selector(sampleRate, rate, shiftRate, withSquelch=False)

        workers = [self.selector]

        # primary demodulator is only necessary if the secondary does not accept IQ input
        if secondaryDemod.getInputFormat() is not Format.COMPLEX_FLOAT:
            workers += [demod]

        workers += [secondaryDemod]

        super().__init__(workers)

    def setBandPass(self, lowCut, highCut):
        self.selector.setBandpass(lowCut, highCut)
