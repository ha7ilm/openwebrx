from csdr.chain import Chain
from pycsdr.modules import FmDemod, Agc, Writer
from pycsdr.types import Format
from digiham.modules import DstarDecoder, DcBlock, FskDemodulator, GfskDemodulator, DigitalVoiceFilter, MbeSynthesizer, NarrowRrcFilter, NxdnDecoder, DmrDecoder, WideRrcFilter, YsfDecoder
from digiham.ambe import Modes


class DigihamChain(Chain):
    def __init__(self, fskDemodulator, decoder, mbeMode, filter=None, codecserver: str = ""):
        self.decoder = decoder
        if codecserver is None:
            codecserver = ""
        agc = Agc(Format.SHORT)
        agc.setMaxGain(30)
        agc.setInitialGain(3)
        workers = [FmDemod(), DcBlock()]
        if filter is not None:
            workers += [filter]
        workers += [
            fskDemodulator,
            decoder,
            MbeSynthesizer(mbeMode, codecserver),
            DigitalVoiceFilter(),
            agc
        ]
        super().__init__(*workers)

    def setMetaWriter(self, writer: Writer):
        self.decoder.setMetaWriter(writer)


class Dstar(DigihamChain):
    def __init__(self, codecserver: str = ""):
        super().__init__(
            fskDemodulator=FskDemodulator(samplesPerSymbol=10),
            decoder=DstarDecoder(),
            mbeMode=Modes.DStarMode,
            codecserver=codecserver
        )


class Nxdn(DigihamChain):
    def __init__(self, codecserver: str = ""):
        super().__init__(
            fskDemodulator=GfskDemodulator(samplesPerSymbol=20),
            decoder=NxdnDecoder(),
            mbeMode=Modes.NxdnMode,
            filter=NarrowRrcFilter(),
            codecserver=codecserver
        )


class Dmr(DigihamChain):
    def __init__(self, codecserver: str = ""):
        super().__init__(
            fskDemodulator=GfskDemodulator(samplesPerSymbol=10),
            decoder=DmrDecoder(),
            mbeMode=Modes.DmrMode,
            filter=WideRrcFilter(),
            codecserver=codecserver,
        )

    def setSlotFilter(self, slotFilter: int) -> None:
        self.decoder.setSlotFilter(slotFilter)


class Ysf(DigihamChain):
    def __init__(self, codecserver: str = ""):
        super().__init__(
            fskDemodulator=GfskDemodulator(samplesPerSymbol=10),
            decoder=YsfDecoder(),
            mbeMode=Modes.YsfMode,
            filter=WideRrcFilter(),
            codecserver=codecserver
        )
