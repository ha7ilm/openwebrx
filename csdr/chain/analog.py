from csdr.chain.demodulator import BaseDemodulatorChain, FixedIfSampleRateChain, HdAudio, DeemphasisTauChain
from pycsdr.modules import AmDemod, DcBlock, FmDemod, Limit, NfmDeemphasis, Agc, WfmDeemphasis, FractionalDecimator, RealPart
from pycsdr.types import Format, AgcProfile


class Am(BaseDemodulatorChain):
    def __init__(self):
        agc = Agc(Format.FLOAT)
        agc.setProfile(AgcProfile.SLOW)
        agc.setInitialGain(200)
        workers = [
            AmDemod(),
            DcBlock(),
            agc,
        ]

        super().__init__(workers)


class NFm(BaseDemodulatorChain):
    def __init__(self, sampleRate: int):
        self.sampleRate = sampleRate
        agc = Agc(Format.FLOAT)
        agc.setProfile(AgcProfile.SLOW)
        agc.setMaxGain(3)
        workers = [
            FmDemod(),
            Limit(),
            NfmDeemphasis(sampleRate),
            agc,
        ]
        super().__init__(workers)

    def setSampleRate(self, sampleRate: int) -> None:
        if sampleRate == self.sampleRate:
            return
        self.sampleRate = sampleRate
        self.replace(2, NfmDeemphasis(sampleRate))


class WFm(BaseDemodulatorChain, FixedIfSampleRateChain, DeemphasisTauChain, HdAudio):
    def __init__(self, sampleRate: int, tau: float):
        self.sampleRate = sampleRate
        self.tau = tau
        workers = [
            FmDemod(),
            Limit(),
            FractionalDecimator(Format.FLOAT, 200000.0 / self.sampleRate, prefilter=True),
            WfmDeemphasis(self.sampleRate, self.tau),
        ]
        super().__init__(workers)

    def getFixedIfSampleRate(self):
        return 200000

    def setDeemphasisTau(self, tau: float) -> None:
        if tau == self.tau:
            return
        self.tau = tau
        self.replace(3, WfmDeemphasis(self.sampleRate, self.tau))

    def setSampleRate(self, sampleRate: int) -> None:
        if sampleRate == self.sampleRate:
            return
        self.sampleRate = sampleRate
        self.replace(2, FractionalDecimator(Format.FLOAT, 200000.0 / self.sampleRate, prefilter=True))
        self.replace(3, WfmDeemphasis(self.sampleRate, self.tau))


class Ssb(BaseDemodulatorChain):
    def __init__(self):
        workers = [
            RealPart(),
            Agc(Format.FLOAT),
        ]
        super().__init__(workers)
