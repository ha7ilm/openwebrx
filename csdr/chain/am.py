from csdr.chain import Chain
from csdr.chain.demodulator import Demodulator
from pycsdr.modules import AmDemod, DcBlock, Agc, Convert
from pycsdr.types import Format


class Am(Demodulator):
    def __init__(self):
        workers = [
            AmDemod(),
            DcBlock(),
            # empty chain as placeholder for the "last decimation"
            Chain(),
            Agc(Format.FLOAT),
            Convert(Format.FLOAT, Format.SHORT),
        ]

        super().__init__(*workers)

    def setLastDecimation(self, decimation: Chain):
        # TODO: build api to replace workers
        # TODO: replace placeholder
        pass
