from csdr.chain import Chain
from pycsdr.modules import FmDemod, Agc, Writer
from pycsdr.types import Format
from digiham.modules import DstarDecoder, DcBlock, FskDemodulator, GfskDemodulator, DigitalVoiceFilter, MbeSynthesizer, NarrowRrcFilter, NxdnDecoder
from digiham.ambe import Modes


class DigihamChain(Chain):
    def __init__(self, codecserver: str = ""):
        if codecserver is None:
            codecserver = ""
        workers = [
            FmDemod(),
            DcBlock(),
            self.fskDemodulator,
            self.decoder,
            MbeSynthesizer(self.mbeMode, codecserver),
            DigitalVoiceFilter(),
            self.agc
        ]
        super().__init__(*workers)

    def setMetaWriter(self, writer: Writer):
        self.decoder.setMetaWriter(writer)


class Dstar(DigihamChain):
    def __init__(self, codecserver: str = ""):
        self.fskDemodulator = FskDemodulator(samplesPerSymbol=10)
        self.decoder = DstarDecoder()
        self.mbeMode = Modes.DStarMode
        self.agc = Agc(Format.SHORT)
        self.agc.setMaxGain(30)
        self.agc.setInitialGain(3)
        super().__init__(codecserver)


class Nxdn(DigihamChain):
    def __init__(self, codecserver: str = ""):
        self.fskDemodulator = GfskDemodulator(samplesPerSymbol=20)
        self.decoder = NxdnDecoder()
        self.mbeMode = Modes.NxdnMode
        self.agc = Agc(Format.SHORT)
        self.agc.setMaxGain(30)
        self.agc.setInitialGain(3)
        super().__init__(codecserver)
