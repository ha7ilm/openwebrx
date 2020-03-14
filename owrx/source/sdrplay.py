from .soapy import SoapyConnectorSource


class SdrplaySource(SoapyConnectorSource):
    def getSoapySettingsMappings(self):
        mappings = super().getSoapySettingsMappings()
        mappings.update({"bias_tee": "biasT_ctrl"})
        return mappings

    def getDriver(self):
        return "sdrplay"
