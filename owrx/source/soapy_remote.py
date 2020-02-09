from .soapy import SoapyConnectorSource


class SoapyRemoteSource(SoapyConnectorSource):
    def getEventNames(self):
        return super().getEventNames() + ["remote", "remote_driver"]

    def getDriver(self):
        return "remote"

    def buildSoapyDeviceParameters(self, parsed, values):
        params = super().buildSoapyDeviceParameters(parsed, values)
        params = [v for v in params if not "remote" in params]
        params += [{"remote": values["remote"]}]
        if "remote_driver" in values and values["remote_driver"] is not None:
            params += [{"remote:driver": values["remote_driver"]}]
        return params
