from .connector import ConnectorSource


class RtlSdrSource(ConnectorSource):
    def __init__(self, id, props):
        super().__init__(id, props)
        self.getCommandMapper().setBase("rtl_connector")
