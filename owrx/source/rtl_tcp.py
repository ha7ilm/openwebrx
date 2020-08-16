from .connector import ConnectorSource
from owrx.command import Flag, Option


class RtlTcpSource(ConnectorSource):
    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setBase("rtl_tcp_connector")
            .setMappings({"bias_tee": Flag("-b"), "direct_sampling": Option("-e")})
        )
