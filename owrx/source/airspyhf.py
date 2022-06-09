from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription


class AirspyhfSource(SoapyConnectorSource):
    def getDriver(self):
        return "airspyhf"


class AirspyhfDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "Airspy HF+ or Discovery"

    def supportsPpm(self):
        # not currently supported by the SoapySDR module.
        return False
