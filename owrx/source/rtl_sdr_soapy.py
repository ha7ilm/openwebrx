from .soapy import SoapyConnectorSource


class RtlSdrSoapySource(SoapyConnectorSource):
    def getDriver(self):
        return "rtlsdr"
