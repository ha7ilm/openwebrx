from owrx.command import Option
from .direct import DirectSource
from subprocess import Popen

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

    def getFormatConversion(self):
        return ["csdr convert_s16_f", "csdr gain_ff 5"]

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
