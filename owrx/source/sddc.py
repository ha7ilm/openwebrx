from owrx.source.connector import ConnectorSource


class SddcSource(ConnectorSource):
    def getCommandMapper(self):
        return super().getCommandMapper().setBase("sddc_connector")
