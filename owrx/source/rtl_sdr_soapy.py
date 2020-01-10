from .soapy import SoapyConnectorSource
from owrx.command import Option


class RtlSdrSoapySource(SoapyConnectorSource):
    def getCommandMapper(self):
        return super().getCommandMapper().setMappings({"direct_sampling": Option("-t direct_samp").setSpacer("=")})

    def getDriver(self):
        return "rtlsdr"

    def getEventNames(self):
        return super().getEventNames() + ["direct_sampling"]
