from owrx.config import Config
from csdr import csdr
import threading
from owrx.source import SdrSource

import logging

logger = logging.getLogger(__name__)


class SpectrumThread(csdr.output):
    def __init__(self, sdrSource):
        self.sdrSource = sdrSource
        super().__init__()

        self.props = props = self.sdrSource.props.collect(
            "samp_rate",
            "fft_size",
            "fft_fps",
            "fft_voverlap_factor",
            "fft_compression",
            "csdr_dynamic_bufsize",
            "csdr_print_bufsizes",
            "csdr_through",
            "temporary_directory",
        ).defaults(Config.get())

        self.dsp = dsp = csdr.dsp(self)
        dsp.nc_port = self.sdrSource.getPort()
        dsp.set_demodulator("fft")

        def set_fft_averages(key, value):
            samp_rate = props["samp_rate"]
            fft_size = props["fft_size"]
            fft_fps = props["fft_fps"]
            fft_voverlap_factor = props["fft_voverlap_factor"]

            dsp.set_fft_averages(
                int(round(1.0 * samp_rate / fft_size / fft_fps / (1.0 - fft_voverlap_factor)))
                if fft_voverlap_factor > 0
                else 0
            )

        self.subscriptions = [
            props.getProperty("samp_rate").wire(dsp.set_samp_rate),
            props.getProperty("fft_size").wire(dsp.set_fft_size),
            props.getProperty("fft_fps").wire(dsp.set_fft_fps),
            props.getProperty("fft_compression").wire(dsp.set_fft_compression),
            props.getProperty("temporary_directory").wire(dsp.set_temporary_directory),
            props.collect("samp_rate", "fft_size", "fft_fps", "fft_voverlap_factor").wire(set_fft_averages),
        ]

        set_fft_averages(None, None)

        dsp.csdr_dynamic_bufsize = props["csdr_dynamic_bufsize"]
        dsp.csdr_print_bufsizes = props["csdr_print_bufsizes"]
        dsp.csdr_through = props["csdr_through"]
        logger.debug("Spectrum thread initialized successfully.")

    def start(self):
        self.sdrSource.addClient(self)
        if self.sdrSource.isAvailable():
            self.dsp.start()

    def supports_type(self, t):
        return t == "audio"

    def receive_output(self, type, read_fn):
        threading.Thread(target=self.pump(read_fn, self.sdrSource.writeSpectrumData)).start()

    def stop(self):
        self.dsp.stop()
        self.sdrSource.removeClient(self)
        for c in self.subscriptions:
            c.cancel()
        self.subscriptions = []

    def getClientClass(self):
        return SdrSource.CLIENT_USER

    def onStateChange(self, state):
        if state in [SdrSource.STATE_STOPPING, SdrSource.STATE_FAILED]:
            self.dsp.stop()
        elif state == SdrSource.STATE_RUNNING:
            self.dsp.start()

    def onBusyStateChange(self, state):
        pass
