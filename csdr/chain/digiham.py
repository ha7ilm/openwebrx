from csdr.chain import Chain
from pycsdr.modules import FmDemod, Agc
from pycsdr.types import Format
from digiham.modules import DstarDecoder, DcBlock, FskDemodulator, GfskDemodulator, DigitalVoiceFilter, MbeSynthesizer, NarrowRrcFilter, NxdnDecoder
from digiham.ambe import Modes


class Dstar(Chain):
    def __init__(self, codecserver: str = ""):
        if codecserver is None:
            codecserver = ""
        agc = Agc(Format.SHORT)
        agc.setMaxGain(30)
        agc.setInitialGain(3)
        workers = [
            FmDemod(),
            DcBlock(),
            FskDemodulator(samplesPerSymbol=10),
            DstarDecoder(),
            MbeSynthesizer(Modes.DStarMode, codecserver),
            DigitalVoiceFilter(),
            agc
        ]
        super().__init__(*workers)


class Nxdn(Chain):
    def __init__(self, codecserver: str = ""):
        if codecserver is None:
            codecserver = ""
        agc = Agc(Format.SHORT)
        agc.setMaxGain(30)
        agc.setInitialGain(3)
        workers = [
            FmDemod(),
            DcBlock(),
            NarrowRrcFilter(),
            GfskDemodulator(samplesPerSymbol=20),
            NxdnDecoder(),
            MbeSynthesizer(Modes.NxdnMode, codecserver),
            DigitalVoiceFilter(),
            agc,
        ]
        super().__init__(*workers)
