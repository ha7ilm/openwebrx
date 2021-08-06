from csdr.chain import Chain
from pycsdr.modules import FmDemod, Agc, Writer
from pycsdr.types import Format
from digiham.modules import DstarDecoder, DcBlock, FskDemodulator, GfskDemodulator, DigitalVoiceFilter, MbeSynthesizer, NarrowRrcFilter, NxdnDecoder, DmrDecoder
from digiham.ambe import Modes


class DigihamChain(Chain):
    def __init__(self, codecserver: str = ""):
        if codecserver is None:
            codecserver = ""
        agc = Agc(Format.SHORT)
        agc.setMaxGain(30)
        agc.setInitialGain(3)
        workers = [
            FmDemod(),
            DcBlock(),
            self.fskDemodulator,
            self.decoder,
            MbeSynthesizer(self.mbeMode, codecserver),
            DigitalVoiceFilter(),
            agc
        ]
        super().__init__(*workers)

    def setMetaWriter(self, writer: Writer):
        self.decoder.setMetaWriter(writer)


class Dstar(DigihamChain):
    def __init__(self, codecserver: str = ""):
        self.fskDemodulator = FskDemodulator(samplesPerSymbol=10)
        self.decoder = DstarDecoder()
        self.mbeMode = Modes.DStarMode
        super().__init__(codecserver)


class Nxdn(DigihamChain):
    def __init__(self, codecserver: str = ""):
        self.fskDemodulator = GfskDemodulator(samplesPerSymbol=20)
        self.decoder = NxdnDecoder()
        self.mbeMode = Modes.NxdnMode
        super().__init__(codecserver)

class Dmr(DigihamChain):
    def __init__(self, codecserver: str = ""):
        self.fskDemodulator = GfskDemodulator(samplesPerSymbol=10)
        self.decoder = DmrDecoder()
        self.mbeMode = Modes.DmrMode
        super().__init__(codecserver)
