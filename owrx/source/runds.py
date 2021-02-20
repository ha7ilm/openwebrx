from owrx.source.connector import ConnectorSource, ConnectorDeviceDescription
from owrx.command import Argument, Flag, Option


class RundsSource(ConnectorSource):
    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setBase("runds_connector")
            .setMappings(
                {
                    "long": Flag("-l"),
                    "remote": Argument(),
                    "protocol": Option("-m"),
                }
            )
        )


class RundsDeviceDescription(ConnectorDeviceDescription):
    pass
