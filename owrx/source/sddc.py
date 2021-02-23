from owrx.source.connector import ConnectorSource, ConnectorDeviceDescription


class SddcSource(ConnectorSource):
    def getCommandMapper(self):
        return super().getCommandMapper().setBase("sddc_connector")


class SddcDeviceDescription(ConnectorDeviceDescription):
    def hasAgc(self):
        return False
