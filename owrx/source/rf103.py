from owrx.source.connector import ConnectorSource


class Rf103Source(ConnectorSource):
    def getCommandMapper(self):
        return super().getCommandMapper().setBase("sddc_connector")
