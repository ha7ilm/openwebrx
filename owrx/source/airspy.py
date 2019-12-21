from .soapy import SoapyConnectorSource


class AirspySource(SoapyConnectorSource):
    def getDriver(self):
        return "airspy"

    def getEventNames(self):
        return super().getEventNames() + ["bias_tee"]

    def getCommand(self):
        cmd = (
                "soapy_connector -p {port} -c {controlPort}".format(port=self.port, controlPort=self.controlPort)
                + ' -s {samp_rate} -f {tuner_freq} -g "{rf_gain}" -P {ppm} -d "{device}"'
        )
        values = self.getCommandValues()
        if values["iqswap"]:
            cmd += " -i"
        if self.rtlProps["rtltcp_compat"]:
            cmd += " -r"
        if values["bias_tee"]:
            cmd += " -t biastee=true"
        return cmd
