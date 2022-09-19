from owrx.command import Option
from owrx.source.direct import DirectSource, DirectSourceDeviceDescription
from subprocess import Popen
from csdr.chain import Chain
from pycsdr.modules import Convert, Gain
from pycsdr.types import Format
from typing import List
from owrx.form.input import Input, TextInput

import logging

logger = logging.getLogger(__name__)


class FifiSdrSource(DirectSource):
    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setBase("arecord")
            .setMappings({"device": Option("-D"), "samp_rate": Option("-r")})
            .setStatic("-t raw -f S16_LE -c2 -")
        )

    def getEventNames(self):
        return super().getEventNames() + ["device"]

    def getFormatConversion(self) -> Chain:
        return Chain([Convert(Format.COMPLEX_SHORT, Format.COMPLEX_FLOAT), Gain(Format.COMPLEX_FLOAT, 5.0)])

    def sendRockProgFrequency(self, frequency):
        process = Popen(["rockprog", "--vco", "-w", "--freq={}".format(frequency / 1e6)])
        process.communicate()
        rc = process.wait()
        if rc != 0:
            logger.warning("rockprog failed to set frequency; rc=%i", rc)

    def preStart(self):
        values = self.getCommandValues()
        self.sendRockProgFrequency(values["tuner_freq"])

    def onPropertyChange(self, changes):
        if "center_freq" in changes:
            self.sendRockProgFrequency(changes["center_freq"])


class FifiSdrDeviceDescription(DirectSourceDeviceDescription):
    def getName(self):
        return "FiFi SDR"

    def supportsPpm(self):
        # not currently mapped, and it's unclear how this should be sent to the device
        return False

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            TextInput(
                "device",
                "Device identifier",
                infotext="Alsa audio device identifier",
            ),
        ]

    def getDeviceOptionalKeys(self):
        return super().getDeviceOptionalKeys() + ["device"]
