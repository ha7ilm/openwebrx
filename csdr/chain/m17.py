from csdr.chain.demodulator import BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain, MetaProvider
from csdr.module.m17 import M17Module
from pycsdr.modules import FmDemod, Limit, Convert, Writer, DcBlock
from pycsdr.types import Format


class M17(BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain, MetaProvider):
    def __init__(self):
        self.module = M17Module()
        workers = [
            FmDemod(),
            DcBlock(),
            Limit(),
            Convert(Format.FLOAT, Format.SHORT),
            self.module,
        ]
        super().__init__(workers)

    def getFixedIfSampleRate(self) -> int:
        return 48000

    def getFixedAudioRate(self) -> int:
        return 8000

    def supportsSquelch(self) -> bool:
        return False

    def setMetaWriter(self, writer: Writer) -> None:
        self.module.setMetaWriter(writer)
