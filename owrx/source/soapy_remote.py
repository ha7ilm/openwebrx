from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input import Input, TextInput
from owrx.form.input.device import RemoteInput
from owrx.form.input.converter import OptionalConverter
from typing import List


class SoapyRemoteSource(SoapyConnectorSource):
    def getEventNames(self):
        return super().getEventNames() + ["remote", "remote_driver"]

    def getDriver(self):
        return "remote"

    def buildSoapyDeviceParameters(self, parsed, values):
        params = super().buildSoapyDeviceParameters(parsed, values)
        params = [v for v in params if "remote" not in params]
        params += [{"remote": values["remote"]}]
        if "remote_driver" in values and values["remote_driver"] is not None:
            params += [{"remote:driver": values["remote_driver"]}]
        return params


class SoapyRemoteDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "Device connected to a SoapyRemote server"

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            RemoteInput(),
            TextInput(
                "remote_driver",
                "Remote driver",
                infotext="SoapySDR driver to be used on the remote SoapySDRServer",
                converter=OptionalConverter(),
            ),
        ]

    def getDeviceMandatoryKeys(self):
        return super().getDeviceMandatoryKeys() + ["remote"]

    def getDeviceOptionalKeys(self):
        return super().getDeviceOptionalKeys() + ["remote_driver"]
