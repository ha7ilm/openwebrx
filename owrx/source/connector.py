from . import SdrSource
from owrx.socket import getAvailablePort
import socket

import logging

logger = logging.getLogger(__name__)


class ConnectorSource(SdrSource):
    def __init__(self, id, props, port):
        super().__init__(id, props, port)
        self.controlSocket = None
        self.controlPort = getAvailablePort()

    def getEventNames(self):
        return [
            "samp_rate",
            "center_freq",
            "ppm",
            "rf_gain",
            "device",
            "iqswap",
            "lfo_offset",
            "rtltcp_compat",
        ]

    def sendControlMessage(self, prop, value):
        logger.debug("sending property change over control socket: {0} changed to {1}".format(prop, value))
        self.controlSocket.sendall("{prop}:{value}\n".format(prop=prop, value=value).encode())

    def wireEvents(self):
        def reconfigure(prop, value):
            if self.monitor is None:
                return
            if (
                    (prop == "center_freq" or prop == "lfo_offset")
                    and "lfo_offset" in self.rtlProps
                    and self.rtlProps["lfo_offset"] is not None
            ):
                freq = self.rtlProps["center_freq"] + self.rtlProps["lfo_offset"]
                self.sendControlMessage("center_freq", freq)
            else:
                self.sendControlMessage(prop, value)

        self.rtlProps.wire(reconfigure)

    def postStart(self):
        logger.debug("opening control socket...")
        self.controlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.controlSocket.connect(("localhost", self.controlPort))

    def stop(self):
        super().stop()
        if self.controlSocket:
            self.controlSocket.close()
            self.controlSocket = None

    def getFormatConversion(self):
        return None

    def useNmux(self):
        return False
