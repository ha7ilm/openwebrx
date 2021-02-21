from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form import Input, TextInput
from owrx.form.device import RemoteInput
from typing import List


class SoapyRemoteSource(SoapyConnectorSource):
    def getEventNames(self):
        return super().getEventNames() + ["remote", "remote_driver"]

    def getDriver(self):
        return "remote"

    def buildSoapyDeviceParameters(self, parsed, values):
        params = super().buildSoapyDeviceParameters(parsed, values)
        params = [v for v in params if not "remote" in params]
        params += [{"remote": values["remote"]}]
        if "remote_driver" in values and values["remote_driver"] is not None:
            params += [{"remote:driver": values["remote_driver"]}]
        return params


class SoapyRemoteDeviceDescription(SoapyConnectorDeviceDescription):
    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            RemoteInput(),
            TextInput(
                "remote_driver", "Remote driver", infotext="SoapySDR driver to be used on the remote SoapySDRServer"
            ),
        ]

    def getOptionalKeys(self):
        return super().getOptionalKeys() + ["remote_driver"]
