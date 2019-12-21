from .connector import ConnectorSource


class SoapyConnectorSource(ConnectorSource):
    """
    must be implemented by child classes to be able to build a driver-based device selector by default.
    return value must be the corresponding soapy driver identifier.
    """
    def getDriver(self):
        pass

    def parseDeviceString(self, dstr):

        def decodeComponent(c):
            kv = c.split("=", 1)
            if len(kv) < 2:
                return c
            else:
                return {kv[0]: kv[1]}

        return [decodeComponent(c) for c in dstr.split(",")]

    def encodeDeviceString(self, dobj):

        def encodeComponent(c):
            if isinstance(c, str):
                return c
            else:
                return ",".join(["{0}={1}".format(key, value) for key, value in c.items()])

        return ",".join([encodeComponent(c) for c in dobj])

    """
    this method always attempts to inject a driver= part into the soapysdr query, depending on what connector was used.
    this prevents the soapy_connector from using the wrong device in scenarios where there's no same-type sdrs.
    """
    def getCommandValues(self):
        values = super().getCommandValues()
        if "device" in values and values["device"] is not None:
            parsed = self.parseDeviceString(values["device"])
            parsed = [v for v in parsed if "driver" not in v]
            parsed += [{"driver": self.getDriver()}]
            values["device"] = self.encodeDeviceString(parsed)
        else:
            values["device"] = "driver={0}".format(self.getDriver())
        return values
