from csdr.chain import Chain
from pycsdr.modules import FmDemod
from digiham.modules import DstarDecoder, DcBlock, FskDemodulator, DigitalVoiceFilter, MbeSynthesizer, NarrowRrcFilter, NxdnDecoder


class Dstar(Chain):
    def __init__(self, codecserver: str = ""):
        workers = [
            FmDemod(),
            DcBlock(),
            FskDemodulator(samplesPerSymbol=10),
            DstarDecoder(),
            MbeSynthesizer(codecserver),
            DigitalVoiceFilter()
        ]
        super().__init__(*workers)


class Nxdn(Chain):
    def __init__(self, codecserver: str = ""):
        workers = [
            FmDemod(),
            DcBlock(),
            NarrowRrcFilter(),
            # todo: switch out with gfsk
            FskDemodulator(samplesPerSymbol=20),
            NxdnDecoder(),
            MbeSynthesizer(codecserver),
            DigitalVoiceFilter()
        ]
        super().__init__(*workers)
