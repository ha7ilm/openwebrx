from csdr.chain.demodulator import BaseDemodulatorChain, FixedAudioRateChain, FixedIfSampleRateChain, DialFrequencyReceiver, MetaProvider, SlotFilterChain, DemodulatorError, ServiceDemodulator
from pycsdr.modules import FmDemod, Agc, Writer, Buffer
from pycsdr.types import Format
from digiham.modules import DstarDecoder, DcBlock, FskDemodulator, GfskDemodulator, DigitalVoiceFilter, MbeSynthesizer, NarrowRrcFilter, NxdnDecoder, DmrDecoder, WideRrcFilter, YsfDecoder, PocsagDecoder
from digiham.ambe import Modes, ServerError
from owrx.meta import MetaParser
from owrx.pocsag import PocsagParser


class DigihamChain(BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain, DialFrequencyReceiver, MetaProvider):
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
        try:
            mbeSynthesizer = MbeSynthesizer(mbeMode, codecserver)
        except ConnectionError as ce:
            raise DemodulatorError("Connection to codecserver failed: {}".format(ce))
        except ServerError as se:
            raise DemodulatorError("Codecserver error: {}".format(se))
        workers += [
            fskDemodulator,
            decoder,
            mbeSynthesizer,
            DigitalVoiceFilter(),
            agc
        ]
        self.metaParser = None
        self.dialFrequency = None
        super().__init__(workers)

    def getFixedIfSampleRate(self):
        return 48000

    def getFixedAudioRate(self):
        return 8000

    def setMetaWriter(self, writer: Writer) -> None:
        if self.metaParser is None:
            self.metaParser = MetaParser()
            buffer = Buffer(Format.CHAR)
            self.decoder.setMetaWriter(buffer)
            self.metaParser.setReader(buffer.getReader())
            if self.dialFrequency is not None:
                self.metaParser.setDialFrequency(self.dialFrequency)
        self.metaParser.setWriter(writer)

    def supportsSquelch(self):
        return False

    def setDialFrequency(self, frequency: int) -> None:
        self.dialFrequency = frequency
        if self.metaParser is None:
            return
        self.metaParser.setDialFrequency(frequency)

    def stop(self):
        if self.metaParser is not None:
            self.metaParser.stop()
        super().stop()


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


class Dmr(DigihamChain, SlotFilterChain):
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


class PocsagDemodulator(ServiceDemodulator, DialFrequencyReceiver):
    def __init__(self):
        self.parser = PocsagParser()
        workers = [
            FmDemod(),
            FskDemodulator(samplesPerSymbol=40, invert=True),
            PocsagDecoder(),
            self.parser,
        ]
        super().__init__(workers)

    def supportsSquelch(self) -> bool:
        return False

    def getFixedAudioRate(self) -> int:
        return 48000

    def setDialFrequency(self, frequency: int) -> None:
        self.parser.setDialFrequency(frequency)
