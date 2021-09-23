from csdr.chain import Chain
from csdr.chain.selector import Selector
from csdr.chain.demodulator import BaseDemodulatorChain, ServiceDemodulator
from pycsdr.types import Format


class ServiceDemodulatorChain(Chain):
    def __init__(self, demod: BaseDemodulatorChain, secondaryDemod: ServiceDemodulator, sampleRate: int, frequencyOffset: int):
        self.selector = Selector(sampleRate, secondaryDemod.getFixedAudioRate(), withSquelch=False)
        self.selector.setFrequencyOffset(frequencyOffset)

        workers = [self.selector]

        # primary demodulator is only necessary if the secondary does not accept IQ input
        if secondaryDemod.getInputFormat() is not Format.COMPLEX_FLOAT:
            workers += [demod]

        workers += [secondaryDemod]

        super().__init__(workers)

    def setBandPass(self, lowCut, highCut):
        self.selector.setBandpass(lowCut, highCut)
