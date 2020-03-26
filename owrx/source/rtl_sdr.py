from .connector import ConnectorSource
from owrx.command import Flag


class RtlSdrSource(ConnectorSource):
    def getCommandMapper(self):
        return super().getCommandMapper().setBase("rtl_connector").setMappings(
            {
                "bias_tee": Flag("-b")
            }
        )

    def getEventNames(self):
        return super().getEventNames() + ["bias_tee"]
