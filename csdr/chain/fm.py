from csdr.chain.demodulator import Demodulator, Chain
from pycsdr.modules import FmDemod, Limit, NfmDeemphasis, Agc, Convert
from pycsdr.types import Format


class Fm(Demodulator):
    def __init__(self, sampleRate: int):
        workers = [
            FmDemod(),
            Limit(),
            # empty chain as placeholder for the "last decimation"
            Chain(),
            NfmDeemphasis(sampleRate),
            Agc(Format.FLOAT),
            Convert(Format.FLOAT, Format.SHORT),
        ]
        super().__init__(*workers)

    def setLastDecimation(self, decimation: Chain):
        self.replace(2, decimation)
