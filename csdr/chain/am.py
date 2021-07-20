from csdr.chain import Chain
from csdr.chain.demodulator import Demodulator
from pycsdr.modules import AmDemod, DcBlock, Agc, Convert
from pycsdr.types import Format, AgcProfile


class Am(Demodulator):
    def __init__(self):
        agc = Agc(Format.FLOAT)
        agc.setProfile(AgcProfile.SLOW)
        agc.setInitialGain(200)
        workers = [
            AmDemod(),
            DcBlock(),
            # empty chain as placeholder for the "last decimation"
            Chain(),
            agc,
            Convert(Format.FLOAT, Format.SHORT),
        ]

        super().__init__(*workers)

    def setLastDecimation(self, decimation: Chain):
        self.replace(2, decimation)
