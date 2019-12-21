from .connector import ConnectorSource


class RtlSdrSource(ConnectorSource):
    def getCommand(self):
        cmd = (
                "rtl_connector -p {port} -c {controlPort}".format(port=self.port, controlPort=self.controlPort)
                + " -s {samp_rate} -f {tuner_freq} -g {rf_gain} -P {ppm}"
        )
        if "device" in self.rtlProps and self.rtlProps["device"] is not None:
            cmd += ' -d "{device}"'
        if self.rtlProps["iqswap"]:
            cmd += " -i"
        if self.rtlProps["rtltcp_compat"]:
            cmd += " -r"
        return cmd
