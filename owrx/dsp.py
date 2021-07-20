from owrx.meta import MetaParser
from owrx.wsjt import WsjtParser
from owrx.js8 import Js8Parser
from owrx.aprs import AprsParser
from owrx.pocsag import PocsagParser
from owrx.source import SdrSourceEventClient, SdrSourceState, SdrClientClass
from owrx.property import PropertyStack, PropertyLayer, PropertyValidator
from owrx.property.validators import OrValidator, RegexValidator, BoolValidator
from owrx.modes import Modes
from owrx.config.core import CoreConfig
from csdr.output import Output
from csdr import Dsp
import threading
import re

import logging

logger = logging.getLogger(__name__)


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
            "wsjt_demod": WsjtParser(self.handler),
            "packet_demod": AprsParser(self.handler),
            "pocsag_demod": PocsagParser(self.handler),
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

        self.dsp = Dsp(self)
        self.dsp.nc_port = self.sdrSource.getPort()

        def set_low_cut(cut):
            bpf = self.dsp.get_bpf()
            bpf[0] = cut
            self.dsp.set_bpf(*bpf)

        def set_high_cut(cut):
            bpf = self.dsp.get_bpf()
            bpf[1] = cut
            self.dsp.set_bpf(*bpf)

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
            self.dsp.set_demodulator(self.props["start_mod"])
            mode = Modes.findByModulation(self.props["start_mod"])

            if mode and mode.bandpass:
                self.dsp.set_bpf(mode.bandpass.low_cut, mode.bandpass.high_cut)
            else:
                self.dsp.set_bpf(-4000, 4000)

        if "start_freq" in self.props and "center_freq" in self.props:
            self.dsp.set_offset_freq(self.props["start_freq"] - self.props["center_freq"])
        else:
            self.dsp.set_offset_freq(0)

        self.subscriptions = [
            self.props.wireProperty("audio_compression", self.dsp.set_audio_compression),
            self.props.wireProperty("fft_compression", self.dsp.set_fft_compression),
            self.props.wireProperty("digimodes_fft_size", self.dsp.set_secondary_fft_size),
            self.props.wireProperty("samp_rate", self.dsp.set_samp_rate),
            self.props.wireProperty("output_rate", self.dsp.set_output_rate),
            self.props.wireProperty("hd_output_rate", self.dsp.set_hd_output_rate),
            self.props.wireProperty("offset_freq", self.dsp.set_offset_freq),
            self.props.wireProperty("center_freq", self.dsp.set_center_freq),
            self.props.wireProperty("squelch_level", self.dsp.set_squelch_level),
            self.props.wireProperty("low_cut", set_low_cut),
            self.props.wireProperty("high_cut", set_high_cut),
            self.props.wireProperty("mod", self.dsp.set_demodulator),
            self.props.wireProperty("dmr_filter", self.dsp.set_dmr_filter),
            self.props.wireProperty("wfm_deemphasis_tau", self.dsp.set_wfm_deemphasis_tau),
            self.props.wireProperty("digital_voice_codecserver", self.dsp.set_codecserver),
            self.props.filter("center_freq", "offset_freq").wire(set_dial_freq),
        ]

        self.dsp.set_temporary_directory(CoreConfig().get_temporary_directory())

        def send_secondary_config(*args):
            self.handler.write_secondary_dsp_config(
                {
                    "secondary_fft_size": self.props["digimodes_fft_size"],
                    "if_samp_rate": self.dsp.if_samp_rate(),
                    "secondary_bw": self.dsp.secondary_bw(),
                }
            )

        def set_secondary_mod(mod):
            if mod == False:
                mod = None
            self.dsp.set_secondary_demodulator(mod)
            if mod is not None:
                send_secondary_config()

        self.subscriptions += [
            self.props.wireProperty("secondary_mod", set_secondary_mod),
            self.props.wireProperty("digimodes_fft_size", send_secondary_config),
            self.props.wireProperty("secondary_offset_freq", self.dsp.set_secondary_offset_freq),
        ]

        self.startOnAvailable = False

        self.sdrSource.addClient(self)

        super().__init__()

    def start(self):
        if self.sdrSource.isAvailable():
            self.dsp.start()
        else:
            self.startOnAvailable = True

    def receive_output(self, t, read_fn):
        logger.debug("adding new output of type %s", t)
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

        threading.Thread(target=self.pump(read_fn, write), name="dsp_pump_{}".format(t)).start()

    def stop(self):
        self.dsp.stop()
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
                self.dsp.start()
                self.startOnAvailable = False
        elif state is SdrSourceState.STOPPING:
            logger.debug("received STATE_STOPPING, shutting down DspSource")
            self.dsp.stop()

    def onFail(self):
        logger.debug("received onFail(), shutting down DspSource")
        self.dsp.stop()

    def onShutdown(self):
        self.dsp.stop()
