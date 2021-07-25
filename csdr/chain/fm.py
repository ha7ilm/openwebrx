from csdr.chain import Chain
from pycsdr.modules import FmDemod, Limit, NfmDeemphasis, Agc, WfmDeemphasis, FractionalDecimator
from pycsdr.types import Format, AgcProfile


class NFm(Chain):
    def __init__(self, sampleRate: int):
        agc = Agc(Format.FLOAT)
        agc.setProfile(AgcProfile.SLOW)
        agc.setMaxGain(3)
        workers = [
            FmDemod(),
            Limit(),
            NfmDeemphasis(sampleRate),
            agc,
        ]
        super().__init__(*workers)


class WFm(Chain):
    def __init__(self, sampleRate: int, tau: float):
        workers = [
            FmDemod(),
            Limit(),
            FractionalDecimator(Format.FLOAT, 200000.0 / sampleRate, prefilter=True),
            WfmDeemphasis(sampleRate, tau),
        ]
        super().__init__(*workers)
