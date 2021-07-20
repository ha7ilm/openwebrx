from csdr.chain.demodulator import Demodulator, Chain
from pycsdr.modules import FmDemod, Limit, NfmDeemphasis, Agc, Convert
from pycsdr.types import Format, AgcProfile


class Fm(Demodulator):
    def __init__(self, sampleRate: int):
        agc = Agc(Format.FLOAT)
        agc.setProfile(AgcProfile.SLOW)
        agc.setMaxGain(3)
        workers = [
            FmDemod(),
            Limit(),
            # empty chain as placeholder for the "last decimation"
            Chain(),
            NfmDeemphasis(sampleRate),
            agc,
            Convert(Format.FLOAT, Format.SHORT),
        ]
        super().__init__(*workers)

    def setLastDecimation(self, decimation: Chain):
        self.replace(2, decimation)
