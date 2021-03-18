from owrx.config.core import CoreConfig
from owrx.config import Config
from csdr import csdr
import threading
from owrx.source import SdrSourceEventClient, SdrSourceState, SdrClientClass
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
        )

        self.dsp = dsp = csdr.dsp(self)
        dsp.nc_port = self.sdrSource.getPort()
        dsp.set_demodulator("fft")

        def set_fft_averages(changes=None):
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
            props.wireProperty("samp_rate", dsp.set_samp_rate),
            props.wireProperty("fft_size", dsp.set_fft_size),
            props.wireProperty("fft_fps", dsp.set_fft_fps),
            props.wireProperty("fft_compression", dsp.set_fft_compression),
            props.filter("samp_rate", "fft_size", "fft_fps", "fft_voverlap_factor").wire(set_fft_averages),
        ]

        set_fft_averages()

        dsp.set_temporary_directory(CoreConfig().get_temporary_directory())
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

    def getClientClass(self) -> SdrClientClass:
        return SdrClientClass.USER

    def onStateChange(self, state: SdrSourceState):
        if state is SdrSourceState.STOPPING:
            self.dsp.stop()
        elif state is SdrSourceState.RUNNING:
            self.dsp.start()

    def onFail(self):
        self.dsp.stop()
