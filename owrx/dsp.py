from owrx.meta import MetaParser
from owrx.wsjt import WsjtParser
from owrx.js8 import Js8Parser
from owrx.source import SdrSourceEventClient, SdrSourceState, SdrClientClass
from owrx.property import PropertyStack, PropertyLayer, PropertyValidator
from owrx.property.validators import OrValidator, RegexValidator, BoolValidator
from owrx.modes import Modes
from csdr.output import Output
from csdr.chain import Chain
from csdr.chain.demodulator import BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain, HdAudio, SecondaryDemodulator, DialFrequencyReceiver
from csdr.chain.selector import Selector
from csdr.chain.clientaudio import ClientAudioChain
from csdr.chain.analog import NFm, WFm, Am, Ssb
from csdr.chain.digiham import DigihamChain, Dmr, Dstar, Nxdn, Ysf
from csdr.chain.fft import FftChain
from csdr.chain.digimodes import AudioChopperDemodulator, PacketDemodulator, PocsagDemodulator
from pycsdr.modules import Buffer, Writer
from pycsdr.types import Format
from typing import Union
import threading
import re

import logging

logger = logging.getLogger(__name__)


class ClientDemodulatorChain(Chain):
    def __init__(self, demod: BaseDemodulatorChain, sampleRate: int, outputRate: int, hdOutputRate: int, audioCompression: str):
        self.sampleRate = sampleRate
        self.outputRate = outputRate
        self.hdOutputRate = hdOutputRate
        self.selector = Selector(sampleRate, outputRate, 0.0)
        self.selector.setBandpass(-4000, 4000)
        self.selectorBuffer = Buffer(Format.COMPLEX_FLOAT)
        self.audioBuffer = None
        self.demodulator = demod
        self.secondaryDemodulator = None
        self.centerFrequency = None
        self.frequencyOffset = None
        inputRate = demod.getFixedAudioRate() if isinstance(demod, FixedAudioRateChain) else outputRate
        oRate = hdOutputRate if isinstance(demod, HdAudio) else outputRate
        self.clientAudioChain = ClientAudioChain(demod.getOutputFormat(), inputRate, oRate, audioCompression)
        self.secondaryFftChain = None
        self.metaWriter = None
        self.secondaryFftWriter = None
        self.secondaryWriter = None
        self.squelchLevel = -150
        super().__init__([self.selector, self.demodulator, self.clientAudioChain])

    def stop(self):
        super().stop()
        if self.secondaryFftChain is not None:
            self.secondaryFftChain.stop()
            self.secondaryFftChain = None
        if self.secondaryDemodulator is not None:
            self.secondaryDemodulator.stop()
            self.secondaryDemodulator = None

    def _connect(self, w1, w2, buffer: Union[Buffer, None] = None) -> None:
        if w1 is self.selector:
            super()._connect(w1, w2, self.selectorBuffer)
        elif w2 is self.clientAudioChain:
            format = w1.getOutputFormat()
            if self.audioBuffer is None or self.audioBuffer.getFormat() != format:
                self.audioBuffer = Buffer(format)
                if self.secondaryDemodulator is not None and self.secondaryDemodulator.getInputFormat() is not Format.COMPLEX_FLOAT:
                    self.secondaryDemodulator.setReader(self.audioBuffer.getReader())
            super()._connect(w1, w2, self.audioBuffer)
        else:
            super()._connect(w1, w2)

    def setDemodulator(self, demodulator: BaseDemodulatorChain):
        if demodulator is self.demodulator:
            return

        try:
            self.clientAudioChain.setFormat(demodulator.getOutputFormat())
        except ValueError:
            # this will happen if the new format does not match the current demodulator.
            # it's expected and should be mended when swapping out the demodulator in the next step
            pass

        self.replace(1, demodulator)

        if self.demodulator is not None:
            self.demodulator.stop()

        self.demodulator = demodulator

        outputRate = self.hdOutputRate if isinstance(self.demodulator, HdAudio) else self.outputRate

        if isinstance(self.demodulator, FixedIfSampleRateChain):
            self.selector.setOutputRate(self.demodulator.getFixedIfSampleRate())
        elif isinstance(self.secondaryDemodulator, FixedAudioRateChain):
            self.selector.setOutputRate(self.secondaryDemodulator.getFixedAudioRate())
        else:
            self.selector.setOutputRate(outputRate)
        self.demodulator.setSampleRate(outputRate)

        if isinstance(self.demodulator, FixedAudioRateChain):
            self.clientAudioChain.setInputRate(self.demodulator.getFixedAudioRate())
        elif isinstance(self.secondaryDemodulator, FixedAudioRateChain):
            self.clientAudioChain.setInputRate(self.secondaryDemodulator.getFixedAudioRate())
        else:
            self.clientAudioChain.setInputRate(outputRate)

        self._syncSquelch()

        self.clientAudioChain.setClientRate(outputRate)

        if self.metaWriter is not None and isinstance(demodulator, DigihamChain):
            demodulator.setMetaWriter(self.metaWriter)

    def _getSelectorOutputRate(self):
        if isinstance(self.secondaryDemodulator, FixedAudioRateChain):
            if isinstance(self.demodulator, FixedAudioRateChain) and self.demodulator.getFixedAudioRate() != self.secondaryDemodulator.getFixedAudioRate():
                raise ValueError("secondary and primary demodulator chain audio rates do not match!")
            return self.secondaryDemodulator.getFixedAudioRate()
        return self.outputRate

    def setSecondaryDemodulator(self, demod: Union[SecondaryDemodulator, None]):
        if demod is self.secondaryDemodulator:
            return

        if self.secondaryDemodulator is not None:
            self.secondaryDemodulator.stop()

        self.secondaryDemodulator = demod

        rate = self._getSelectorOutputRate()
        self.selector.setOutputRate(rate)
        self.clientAudioChain.setInputRate(rate)
        self.demodulator.setSampleRate(rate)
        self._updateDialFrequency()
        self._syncSquelch()

        if self.secondaryDemodulator is not None:
            if self.secondaryDemodulator.getInputFormat() is Format.COMPLEX_FLOAT:
                self.secondaryDemodulator.setReader(self.selectorBuffer.getReader())
            else:
                self.secondaryDemodulator.setReader(self.audioBuffer.getReader())
            self.secondaryDemodulator.setWriter(self.secondaryWriter)

        if self.secondaryDemodulator is None and self.secondaryFftChain is not None:
            self.secondaryFftChain.stop()
            self.secondaryFftChain = None

        if self.secondaryDemodulator is not None and self.secondaryFftChain is None:
            # TODO eliminate constants
            self.secondaryFftChain = FftChain(self._getSelectorOutputRate(), 2048, 0.3, 9, "adpcm")
            self.secondaryFftChain.setReader(self.selectorBuffer.getReader())
            self.secondaryFftChain.setWriter(self.secondaryFftWriter)

        if self.secondaryFftChain is not None:
            self.secondaryFftChain.setSampleRate(rate)

    def _syncSquelch(self):
        if not self.demodulator.supportsSquelch() or (self.secondaryDemodulator is not None and not self.secondaryDemodulator.supportsSquelch()):
            self.selector.setSquelchLevel(-150)
        else:
            self.selector.setSquelchLevel(self.squelchLevel)

    def setLowCut(self, lowCut):
        self.selector.setLowCut(lowCut)

    def setHighCut(self, highCut):
        self.selector.setHighCut(highCut)

    def setBandpass(self, lowCut, highCut):
        self.selector.setBandpass(lowCut, highCut)

    def setFrequencyOffset(self, offset: int) -> None:
        if offset == self.frequencyOffset:
            return
        self.frequencyOffset = offset

        shift = -offset / self.sampleRate
        self.selector.setShiftRate(shift)

        self._updateDialFrequency()

    def setCenterFrequency(self, frequency: int) -> None:
        if frequency == self.centerFrequency:
            return
        self.centerFrequency = frequency
        self._updateDialFrequency()

    def _updateDialFrequency(self):
        if self.centerFrequency is None or self.frequencyOffset is None:
            return
        dialFrequency = self.centerFrequency + self.frequencyOffset
        if isinstance(self.secondaryDemodulator, DialFrequencyReceiver):
            self.secondaryDemodulator.setDialFrequency(dialFrequency)

    def setAudioCompression(self, compression: str) -> None:
        self.clientAudioChain.setAudioCompression(compression)

    def setSquelchLevel(self, level: float) -> None:
        if level == self.squelchLevel:
            return
        self.squelchLevel = level
        self._syncSquelch()

    def setOutputRate(self, outputRate) -> None:
        if outputRate == self.outputRate:
            return

        self.outputRate = outputRate

        if isinstance(self.demodulator, HdAudio):
            return
        if not isinstance(self.demodulator, FixedIfSampleRateChain):
            self.selector.setOutputRate(outputRate)
            self.demodulator.setSampleRate(outputRate)
        if not isinstance(self.demodulator, FixedAudioRateChain):
            self.clientAudioChain.setClientRate(outputRate)

    def setHdOutputRate(self, outputRate) -> None:
        if outputRate == self.hdOutputRate:
            return

        self.hdOutputRate = outputRate

        if not isinstance(self.demodulator, HdAudio):
            return
        if not isinstance(self.demodulator, FixedIfSampleRateChain):
            self.selector.setOutputRate(outputRate)
        if not isinstance(self.demodulator, FixedAudioRateChain):
            self.clientAudioChain.setClientRate(outputRate)

    def setSampleRate(self, sampleRate: int) -> None:
        if sampleRate == self.sampleRate:
            return
        self.sampleRate = sampleRate
        self.selector.setInputRate(sampleRate)
        # TODO update secondary FFT

    def setPowerWriter(self, writer: Writer) -> None:
        self.selector.setPowerWriter(writer)

    def setMetaWriter(self, writer: Writer) -> None:
        if writer is self.metaWriter:
            return
        self.metaWriter = writer
        if isinstance(self.demodulator, DigihamChain):
            self.demodulator.setMetaWriter(self.metaWriter)

    def setSecondaryFftWriter(self, writer: Writer) -> None:
        if writer is self.secondaryFftWriter:
            return
        self.secondaryFftWriter = writer

        if self.secondaryFftChain is not None:
            self.secondaryFftChain.setWriter(writer)

    def setSecondaryWriter(self, writer: Writer) -> None:
        if writer is self.secondaryWriter:
            return
        self.secondaryWriter = writer
        if self.secondaryDemodulator is not None:
            self.secondaryDemodulator.setWriter(writer)

    def setSecondaryFftSize(self, size: int) -> None:
        # TODO
        pass


class ModulationValidator(OrValidator):
    """
    This validator only allows alphanumeric characters and numbers, but no spaces or special characters
    """

    def __init__(self):
        super().__init__(BoolValidator(), RegexValidator(re.compile("^[a-z0-9]+$")))


class DspManager(Output, SdrSourceEventClient):
    def __init__(self, handler, sdrSource):
        self.handler = handler
        self.sdrSource = sdrSource
        self.parsers = {
            "meta": MetaParser(self.handler),
            "js8_demod": Js8Parser(self.handler),
        }

        self.props = PropertyStack()

        # local demodulator properties not forwarded to the sdr
        # ensure strict validation since these can be set from the client
        # and are used to build executable commands
        validators = {
            "output_rate": "int",
            "hd_output_rate": "int",
            "squelch_level": "num",
            "secondary_mod": ModulationValidator(),
            "low_cut": "num",
            "high_cut": "num",
            "offset_freq": "int",
            "mod": ModulationValidator(),
            "secondary_offset_freq": "int",
            "dmr_filter": "int",
        }
        self.localProps = PropertyValidator(PropertyLayer().filter(*validators.keys()), validators)

        self.props.addLayer(0, self.localProps)
        # properties that we inherit from the sdr
        self.props.addLayer(
            1,
            self.sdrSource.getProps().filter(
                "audio_compression",
                "fft_compression",
                "digimodes_fft_size",
                "samp_rate",
                "center_freq",
                "start_mod",
                "start_freq",
                "wfm_deemphasis_tau",
                "digital_voice_codecserver",
            ),
        )

        # TODO wait for the rate to come from the client
        if "output_rate" not in self.props:
            self.props["output_rate"] = 12000
        if "hd_output_rate" not in self.props:
            self.props["hd_output_rate"] = 48000

        self.chain = ClientDemodulatorChain(
            self._getDemodulator("nfm"),
            self.props["samp_rate"],
            self.props["output_rate"],
            self.props["hd_output_rate"],
            self.props["audio_compression"]
        )

        self.readers = {}

        # wire audio output
        buffer = Buffer(self.chain.getOutputFormat())
        self.chain.setWriter(buffer)
        # TODO check for hd audio
        self.wireOutput("audio", buffer)

        # wire power level output
        buffer = Buffer(Format.FLOAT)
        self.chain.setPowerWriter(buffer)
        self.wireOutput("smeter", buffer)

        # wire meta output
        buffer = Buffer(Format.CHAR)
        self.chain.setMetaWriter(buffer)
        self.wireOutput("meta", buffer)

        # wire secondary FFT
        # TODO format is different depending on compression
        buffer = Buffer(Format.CHAR)
        self.chain.setSecondaryFftWriter(buffer)
        self.wireOutput("secondary_fft", buffer)

        # wire secondary demodulator
        buffer = Buffer(Format.CHAR)
        self.chain.setSecondaryWriter(buffer)
        # TODO there's multiple outputs depending on the modulation right now
        self.wireOutput("secondary_demod", buffer)

        def set_dial_freq(changes):
            if (
                "center_freq" not in self.props
                or self.props["center_freq"] is None
                or "offset_freq" not in self.props
                or self.props["offset_freq"] is None
            ):
                return
            freq = self.props["center_freq"] + self.props["offset_freq"]
            for parser in self.parsers.values():
                parser.setDialFrequency(freq)

        if "start_mod" in self.props:
            self.setDemodulator(self.props["start_mod"])
            mode = Modes.findByModulation(self.props["start_mod"])

            if mode and mode.bandpass:
                bpf = [mode.bandpass.low_cut, mode.bandpass.high_cut]
                self.chain.setBandpass(*bpf)

        if "start_freq" in self.props and "center_freq" in self.props:
            self.chain.setFrequencyOffset(self.props["start_freq"] - self.props["center_freq"])
        else:
            self.chain.setFrequencyOffset(0)

        self.subscriptions = [
            self.props.wireProperty("audio_compression", self.setAudioCompression),
            # probably unused:
            # self.props.wireProperty("fft_compression", self.dsp.set_fft_compression),
            self.props.wireProperty("digimodes_fft_size", self.chain.setSecondaryFftSize),
            self.props.wireProperty("samp_rate", self.chain.setSampleRate),
            self.props.wireProperty("output_rate", self.chain.setOutputRate),
            self.props.wireProperty("hd_output_rate", self.chain.setHdOutputRate),
            self.props.wireProperty("offset_freq", self.chain.setFrequencyOffset),
            self.props.wireProperty("center_freq", self.chain.setCenterFrequency),
            self.props.wireProperty("squelch_level", self.chain.setSquelchLevel),
            self.props.wireProperty("low_cut", self.chain.setLowCut),
            self.props.wireProperty("high_cut", self.chain.setHighCut),
            self.props.wireProperty("mod", self.setDemodulator),
            # TODO
            # self.props.wireProperty("dmr_filter", self.dsp.set_dmr_filter),
            # TODO
            # self.props.wireProperty("wfm_deemphasis_tau", self.dsp.set_wfm_deemphasis_tau),
            # TODO
            # self.props.wireProperty("digital_voice_codecserver", self.dsp.set_codecserver),
            self.props.filter("center_freq", "offset_freq").wire(set_dial_freq),
        ]

        # TODO
        # sp.set_temporary_directory(CoreConfig().get_temporary_directory())

        def set_secondary_mod(mod):
            if mod == False:
                mod = None
            self.dsp.set_secondary_demodulator(mod)
            #if mod is not None:
                #send_secondary_config()

        self.subscriptions += [
            self.props.wireProperty("secondary_mod", self.setSecondaryDemodulator),
            self.props.wireProperty("digimodes_fft_size", self.chain.setSecondaryFftSize),
            # TODO
            # self.props.wireProperty("secondary_offset_freq", self.dsp.set_secondary_offset_freq),
        ]

        self.startOnAvailable = False

        self.sdrSource.addClient(self)

        super().__init__()

    def _getDemodulator(self, demod: Union[str, BaseDemodulatorChain]):
        if isinstance(demod, BaseDemodulatorChain):
            return demod
        # TODO: move this to Modes
        demodChain = None
        if demod == "nfm":
            demodChain = NFm(self.props["output_rate"])
        elif demod == "wfm":
            demodChain = WFm(self.props["hd_output_rate"], self.props["wfm_deemphasis_tau"])
        elif demod == "am":
            demodChain = Am()
        elif demod in ["usb", "lsb", "cw"]:
            demodChain = Ssb()
        elif demod == "dmr":
            demodChain = Dmr(self.props["digital_voice_codecserver"])
        elif demod == "dstar":
            demodChain = Dstar(self.props["digital_voice_codecserver"])
        elif demod == "ysf":
            demodChain = Ysf(self.props["digital_voice_codecserver"])
        elif demod == "nxdn":
            demodChain = Nxdn(self.props["digital_voice_codecserver"])

        return demodChain

    def setDemodulator(self, mod):
        demodulator = self._getDemodulator(mod)
        if demodulator is None:
            raise ValueError("unsupported demodulator: {}".format(mod))
        self.chain.setDemodulator(demodulator)

        # re-wire the audio to the correct client API
        buffer = Buffer(self.chain.getOutputFormat())
        self.chain.setWriter(buffer)
        if isinstance(demodulator, HdAudio):
            self.wireOutput("hd_audio", buffer)
        else:
            self.wireOutput("audio", buffer)

    def sendSecondaryConfig(self):
        self.handler.write_secondary_dsp_config(
            {
                "secondary_fft_size": self.props["digimodes_fft_size"],
                "if_samp_rate": self.props["output_rate"],
                # TODO
                "secondary_bw": 31.25
            }
        )

    def _getSecondaryDemodulator(self, mod):
        if isinstance(mod, SecondaryDemodulator):
            return mod
        # TODO add remaining modes
        if mod in ["ft8", "wspr", "jt65", "jt9", "ft4", "fst4", "fst4w", "q65"]:
            return AudioChopperDemodulator(mod, WsjtParser())
        elif mod == "packet":
            return PacketDemodulator()
        elif mod == "pocsag":
            return PocsagDemodulator()
        return None

    def setSecondaryDemodulator(self, mod):
        demodulator = self._getSecondaryDemodulator(mod)
        if not demodulator:
            self.chain.setSecondaryDemodulator(None)
        else:
            self.sendSecondaryConfig()
            self.chain.setSecondaryDemodulator(demodulator)

    def setAudioCompression(self, comp):
        try:
            self.chain.setAudioCompression(comp)
        except ValueError:
            # wrong output format... need to re-wire
            buffer = Buffer(self.chain.getOutputFormat())
            self.chain.setWriter(buffer)
            # TODO check if this is hd audio
            self.wireOutput("audio", buffer)

    def start(self):
        if self.sdrSource.isAvailable():
            self.chain.setReader(self.sdrSource.getBuffer().getReader())
        else:
            self.startOnAvailable = True

    def unwireOutput(self, t: str):
        if t in self.readers:
            self.readers[t].stop()
            del self.readers[t]

    def wireOutput(self, t: str, buffer: Buffer):
        logger.debug("wiring new output of type %s", t)
        writers = {
            "audio": self.handler.write_dsp_data,
            "hd_audio": self.handler.write_hd_audio,
            "smeter": self.handler.write_s_meter_level,
            "secondary_fft": self.handler.write_secondary_fft,
            "secondary_demod": self.handler.write_secondary_demod,
        }
        for demod, parser in self.parsers.items():
            writers[demod] = parser.parse

        write = writers[t]

        self.unwireOutput(t)

        reader = buffer.getReader()
        self.readers[t] = reader
        threading.Thread(target=self.pump(reader.read, write), name="dsp_pump_{}".format(t)).start()

    def stop(self):
        self.chain.stop()
        self.chain = None
        for reader in self.readers.values():
            reader.stop()
        self.readers = {}

        self.startOnAvailable = False
        self.sdrSource.removeClient(self)
        for sub in self.subscriptions:
            sub.cancel()
        self.subscriptions = []

    def setProperties(self, props):
        for k, v in props.items():
            self.setProperty(k, v)

    def setProperty(self, prop, value):
        self.localProps[prop] = value

    def getClientClass(self) -> SdrClientClass:
        return SdrClientClass.USER

    def onStateChange(self, state: SdrSourceState):
        if state is SdrSourceState.RUNNING:
            logger.debug("received STATE_RUNNING, attempting DspSource restart")
            if self.startOnAvailable:
                self.chain.setReader(self.sdrSource.getBuffer().getReader())
                self.startOnAvailable = False
        elif state is SdrSourceState.STOPPING:
            logger.debug("received STATE_STOPPING, shutting down DspSource")
            self.stop()

    def onFail(self):
        logger.debug("received onFail(), shutting down DspSource")
        self.stop()

    def onShutdown(self):
        self.stop()
