from owrx.source.connector import ConnectorSource
from owrx.command import Argument


class Eb200Source(ConnectorSource):
    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setBase("eb200_connector")
            .setMappings({
                "remote": Argument(),
            })
        )
