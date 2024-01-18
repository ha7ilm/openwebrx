from csdr.chain.demodulator import BaseDemodulatorChain, FixedIfSampleRateChain, HdAudio, DeemphasisTauChain, MetaProvider
from pycsdr.modules import AmDemod, DcBlock, FmDemod, Limit, NfmDeemphasis, Agc, WfmDeemphasis, FractionalDecimator, \
    RealPart, Writer, Buffer
from pycsdr.types import Format, AgcProfile
from csdr.chain.redsea import Redsea
from typing import Optional
from owrx.feature import FeatureDetector


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


class WFm(BaseDemodulatorChain, FixedIfSampleRateChain, DeemphasisTauChain, HdAudio, MetaProvider):
    def __init__(self, sampleRate: int, tau: float):
        self.sampleRate = sampleRate
        self.tau = tau
        self.limit = Limit()
        # this buffer is used to tap into the raw audio stream for redsea RDS decoding
        self.metaTapBuffer = Buffer(Format.FLOAT)
        workers = [
            FmDemod(),
            self.limit,
            FractionalDecimator(Format.FLOAT, 200000.0 / self.sampleRate, prefilter=True),
            WfmDeemphasis(self.sampleRate, self.tau),
        ]
        self.metaChain = None
        super().__init__(workers)

    def _connect(self, w1, w2, buffer: Optional[Buffer] = None) -> None:
        if w1 is self.limit:
            buffer = self.metaTapBuffer
        super()._connect(w1, w2, buffer)

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

    def setMetaWriter(self, writer: Writer) -> None:
        if not FeatureDetector().is_available("redsea"):
            return
        if self.metaChain is None:
            self.metaChain = Redsea(self.getFixedIfSampleRate())
            self.metaChain.setReader(self.metaTapBuffer.getReader())
        self.metaChain.setWriter(writer)


class Ssb(BaseDemodulatorChain):
    def __init__(self):
        workers = [
            RealPart(),
            Agc(Format.FLOAT),
        ]
        super().__init__(workers)


class Empty(BaseDemodulatorChain):
    def __init__(self):
        super().__init__([])

    def getOutputFormat(self) -> Format:
        return Format.FLOAT

    def setWriter(self, writer):
        pass
