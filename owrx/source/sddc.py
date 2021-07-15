from owrx.source.connector import ConnectorSource, ConnectorDeviceDescription


class SddcSource(ConnectorSource):
    def getCommandMapper(self):
        return super().getCommandMapper().setBase("sddc_connector")


class SddcDeviceDescription(ConnectorDeviceDescription):
    def getName(self):
        return "BBRF103 / RX666 / RX888 device (libsddc)"

    def hasAgc(self):
        return False
