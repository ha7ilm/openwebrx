from owrx.config import PropertyManager
from owrx.meta import MetaParser
from owrx.wsjt import WsjtParser
from owrx.aprs import AprsParser
from owrx.source import SdrSource
from csdr import csdr
import threading

import logging

logger = logging.getLogger(__name__)


class DspManager(csdr.output):
    def __init__(self, handler, sdrSource):
        self.handler = handler
        self.sdrSource = sdrSource
        self.metaParser = MetaParser(self.handler)
        self.wsjtParser = WsjtParser(self.handler)
        self.aprsParser = AprsParser(self.handler)

        self.localProps = (
            self.sdrSource.getProps()
            .collect(
                "audio_compression",
                "fft_compression",
                "digimodes_fft_size",
                "csdr_dynamic_bufsize",
                "csdr_print_bufsizes",
                "csdr_through",
                "digimodes_enable",
                "samp_rate",
                "digital_voice_unvoiced_quality",
                "dmr_filter",
                "temporary_directory",
                "center_freq",
            )
            .defaults(PropertyManager.getSharedInstance())
        )

        self.dsp = csdr.dsp(self)
        self.dsp.nc_port = self.sdrSource.getPort()

        def set_low_cut(cut):
            bpf = self.dsp.get_bpf()
            bpf[0] = cut
            self.dsp.set_bpf(*bpf)

        def set_high_cut(cut):
            bpf = self.dsp.get_bpf()
            bpf[1] = cut
            self.dsp.set_bpf(*bpf)

        def set_dial_freq(key, value):
            freq = self.localProps["center_freq"] + self.localProps["offset_freq"]
            self.wsjtParser.setDialFrequency(freq)
            self.aprsParser.setDialFrequency(freq)
            self.metaParser.setDialFrequency(freq)

        self.subscriptions = [
            self.localProps.getProperty("audio_compression").wire(self.dsp.set_audio_compression),
            self.localProps.getProperty("fft_compression").wire(self.dsp.set_fft_compression),
            self.localProps.getProperty("digimodes_fft_size").wire(self.dsp.set_secondary_fft_size),
            self.localProps.getProperty("samp_rate").wire(self.dsp.set_samp_rate),
            self.localProps.getProperty("output_rate").wire(self.dsp.set_output_rate),
            self.localProps.getProperty("offset_freq").wire(self.dsp.set_offset_freq),
            self.localProps.getProperty("squelch_level").wire(self.dsp.set_squelch_level),
            self.localProps.getProperty("low_cut").wire(set_low_cut),
            self.localProps.getProperty("high_cut").wire(set_high_cut),
            self.localProps.getProperty("mod").wire(self.dsp.set_demodulator),
            self.localProps.getProperty("digital_voice_unvoiced_quality").wire(self.dsp.set_unvoiced_quality),
            self.localProps.getProperty("dmr_filter").wire(self.dsp.set_dmr_filter),
            self.localProps.getProperty("temporary_directory").wire(self.dsp.set_temporary_directory),
            self.localProps.collect("center_freq", "offset_freq").wire(set_dial_freq),
        ]

        self.dsp.set_offset_freq(0)
        self.dsp.set_bpf(-4000, 4000)
        self.dsp.csdr_dynamic_bufsize = self.localProps["csdr_dynamic_bufsize"]
        self.dsp.csdr_print_bufsizes = self.localProps["csdr_print_bufsizes"]
        self.dsp.csdr_through = self.localProps["csdr_through"]

        if self.localProps["digimodes_enable"]:

            def set_secondary_mod(mod):
                if mod == False:
                    mod = None
                self.dsp.set_secondary_demodulator(mod)
                if mod is not None:
                    self.handler.write_secondary_dsp_config(
                        {
                            "secondary_fft_size": self.localProps["digimodes_fft_size"],
                            "if_samp_rate": self.dsp.if_samp_rate(),
                            "secondary_bw": self.dsp.secondary_bw(),
                        }
                    )

            self.subscriptions += [
                self.localProps.getProperty("secondary_mod").wire(set_secondary_mod),
                self.localProps.getProperty("secondary_offset_freq").wire(self.dsp.set_secondary_offset_freq),
            ]

        self.sdrSource.addClient(self)

        super().__init__()

    def start(self):
        if self.sdrSource.isAvailable():
            self.dsp.start()

    def receive_output(self, t, read_fn):
        logger.debug("adding new output of type %s", t)
        writers = {
            "audio": self.handler.write_dsp_data,
            "smeter": self.handler.write_s_meter_level,
            "secondary_fft": self.handler.write_secondary_fft,
            "secondary_demod": self.handler.write_secondary_demod,
            "meta": self.metaParser.parse,
            "wsjt_demod": self.wsjtParser.parse,
            "packet_demod": self.aprsParser.parse,
        }
        write = writers[t]

        threading.Thread(target=self.pump(read_fn, write)).start()

    def stop(self):
        self.dsp.stop()
        self.sdrSource.removeClient(self)
        for sub in self.subscriptions:
            sub.cancel()
        self.subscriptions = []

    def setProperty(self, prop, value):
        self.localProps.getProperty(prop).setValue(value)

    def getClientClass(self):
        return SdrSource.CLIENT_USER

    def onStateChange(self, state):
        if state == SdrSource.STATE_RUNNING:
            logger.debug("received STATE_RUNNING, attempting DspSource restart")
            self.dsp.start()
        elif state == SdrSource.STATE_STOPPING:
            logger.debug("received STATE_STOPPING, shutting down DspSource")
            self.dsp.stop()
        elif state == SdrSource.STATE_FAILED:
            logger.debug("received STATE_FAILED, shutting down DspSource")
            self.dsp.stop()

    def onBusyStateChange(self, state):
        pass
