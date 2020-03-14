from owrx.command import Flag
from .soapy import SoapyConnectorSource


class AirspySource(SoapyConnectorSource):
    def getSoapySettingsMappings(self):
        mappings = super().getSoapySettingsMappings()
        mappings.update({"bias_tee": "biastee"})
        return mappings

    def getDriver(self):
        return "airspy"
