from .connector import ConnectorSource


class RtlSdrSource(ConnectorSource):
    def __init__(self, id, props, port):
        super().__init__(id, props, port)
        self.getCommandMapper().setBase("rtl_connector")
