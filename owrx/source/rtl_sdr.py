from .connector import ConnectorSource


class RtlSdrSource(ConnectorSource):
    def getCommandMapper(self):
        return super().getCommandMapper().setBase("rtl_connector")
