from .soapy import SoapyConnectorSource


class SdrplaySource(SoapyConnectorSource):
    def getDriver(self):
        return "sdrplay"

    def getEventNames(self):
        return super().getEventNames() + ["antenna"]

    def getCommand(self):
        cmd = (
                "soapy_connector -p {port} -c {controlPort}".format(port=self.port, controlPort=self.controlPort)
                + ' -s {samp_rate} -f {tuner_freq} -g "{rf_gain}" -P {ppm} -a "{antenna}" -d "{device}"'
        )
        values = self.getCommandValues()
        if values["iqswap"]:
            cmd += " -i"
        if self.rtlProps["rtltcp_compat"]:
            cmd += " -r"
        return cmd
