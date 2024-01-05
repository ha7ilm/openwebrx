from owrx.source import SdrSource, SdrDeviceDescription
from owrx.socket import getAvailablePort
from owrx.property import PropertyDeleted
import socket
from owrx.command import Flag, Option
from typing import List
from owrx.form.input import Input, NumberInput, CheckboxInput


class ConnectorSource(SdrSource):
    def __init__(self, id, props):
        self.controlSocket = None
        self.controlPort = getAvailablePort()
        super().__init__(id, props)

    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setMappings(
                {
                    "samp_rate": Option("-s"),
                    "tuner_freq": Option("-f"),
                    "port": Option("-p"),
                    "controlPort": Option("-c"),
                    "device": Option("-d"),
                    "iqswap": Flag("-i"),
                    "rtltcp_compat": Option("-r"),
                    "ppm": Option("-P"),
                    "rf_gain": Option("-g"),
                }
            )
        )

    def sendControlMessage(self, changes):
        for prop, value in changes.items():
            if value is PropertyDeleted:
                value = None
            self.logger.debug("sending property change over control socket: {0} changed to {1}".format(prop, value))
            self.controlSocket.sendall("{prop}:{value}\n".format(prop=prop, value=value).encode())

    def onPropertyChange(self, changes):
        if self.monitor is None:
            return
        if (
            ("center_freq" in changes or "lfo_offset" in changes)
            and "lfo_offset" in self.sdrProps
            and self.sdrProps["lfo_offset"] is not None
        ):
            changes["center_freq"] = self.sdrProps["center_freq"] + self.sdrProps["lfo_offset"]
            changes.pop("lfo_offset", None)
        self.sendControlMessage(changes)

    def postStart(self):
        self.logger.debug("opening control socket...")
        self.controlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.controlSocket.connect(("localhost", self.controlPort))

    def stop(self):
        super().stop()
        if self.controlSocket:
            self.controlSocket.close()
            self.controlSocket = None

    def getControlPort(self):
        return self.controlPort

    def getCommandValues(self):
        values = super().getCommandValues()
        values["port"] = self.getPort()
        values["controlPort"] = self.getControlPort()
        return values


class ConnectorDeviceDescription(SdrDeviceDescription):
    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            NumberInput(
                "rtltcp_compat",
                "Port for rtl_tcp compatible data",
                infotext="Activate an rtl_tcp compatible interface on the port number specified.<br />"
                + "Note: Port is only available on the local machine, not on the network.<br />"
                + "Note: IQ data may be degraded by the downsampling process to 8 bits.",
            ),
            CheckboxInput(
                "iqswap",
                "Swap I and Q channels",
                infotext="Swapping inverts the spectrum, so this is useful in combination with an inverting mixer",
            ),
        ]

    def getDeviceOptionalKeys(self):
        return super().getDeviceOptionalKeys() + ["rtltcp_compat", "iqswap"]

    def getProfileOptionalKeys(self):
        return super().getProfileOptionalKeys() + ["iqswap"]
