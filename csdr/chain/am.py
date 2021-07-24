from csdr.chain import Chain
from pycsdr.modules import AmDemod, DcBlock, Agc, Convert
from pycsdr.types import Format, AgcProfile


class Am(Chain):
    def __init__(self):
        agc = Agc(Format.FLOAT)
        agc.setProfile(AgcProfile.SLOW)
        agc.setInitialGain(200)
        workers = [
            AmDemod(),
            DcBlock(),
            agc,
            Convert(Format.FLOAT, Format.SHORT),
        ]

        super().__init__(*workers)
