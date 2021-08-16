from csdr.chain import Chain
from pycsdr.modules import RealPart, Agc, Convert
from pycsdr.types import Format


class Ssb(Chain):
    def __init__(self):
        workers = [
            RealPart(),
            Agc(Format.FLOAT),
        ]
        super().__init__(*workers)
