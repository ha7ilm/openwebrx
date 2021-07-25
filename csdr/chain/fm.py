from csdr.chain import Chain
from pycsdr.modules import FmDemod, Limit, NfmDeemphasis, Agc, Convert
from pycsdr.types import Format, AgcProfile


class Fm(Chain):
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
