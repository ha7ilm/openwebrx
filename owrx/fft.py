from owrx.config import Config
from csdr import csdr
import threading
from owrx.source import SdrSource, SdrSourceEventClient
from owrx.property import PropertyStack

import logging

logger = logging.getLogger(__name__)


class SpectrumThread(csdr.output, SdrSourceEventClient):
    def __init__(self, sdrSource):
        self.sdrSource = sdrSource
        super().__init__()

        stack = PropertyStack()
        stack.addLayer(0, self.sdrSource.props)
        stack.addLayer(1, Config.get())
        self.props = props = stack.filter(
            "samp_rate",
            "fft_size",
            "fft_fps",
            "fft_voverlap_factor",
            "fft_compression",
            "csdr_dynamic_bufsize",
            "csdr_print_bufsizes",
            "csdr_through",
            "temporary_directory",
        )

        self.dsp = dsp = csdr.dsp(self)
        dsp.nc_port = self.sdrSource.getPort()
        dsp.setBuffer(self.sdrSource.getBuffer())
        dsp.set_demodulator("fft")

        self.subscriptions = [
            props.wireProperty("samp_rate", dsp.set_samp_rate),
            props.wireProperty("fft_size", dsp.set_fft_size),
            props.wireProperty("fft_fps", dsp.set_fft_fps),
            props.wireProperty("fft_compression", dsp.set_fft_compression),
            props.wireProperty("temporary_directory", dsp.set_temporary_directory),
            props.wireProperty("fft_voverlap_factor", dsp.set_fft_voverlap_factor),
        ]

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
