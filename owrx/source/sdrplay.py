from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription


class SdrplaySource(SoapyConnectorSource):
    def getSoapySettingsMappings(self):
        mappings = super().getSoapySettingsMappings()
        mappings.update(
            {
                "bias_tee": "biasT_ctrl",
                "rf_notch": "rfnotch_ctrl",
                "dab_notch": "dabnotch_ctrl",
                "if_mode": "if_mode",
                "external_reference": "extref_ctrl",
            }
        )
        return mappings

    def getDriver(self):
        return "sdrplay"


class SdrplayDeviceDescription(SoapyConnectorDeviceDescription):
    pass
