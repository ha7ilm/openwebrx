from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input import Input, CheckboxInput, DropdownInput, DropdownEnum
from owrx.form.input.device import BiasTeeInput
from owrx.form.input.validator import Range
from typing import List


class SdrplaySource(SoapyConnectorSource):
    def getSoapySettingsMappings(self):
        mappings = super().getSoapySettingsMappings()
        mappings.update(
            {
                "bias_tee": "biasT_ctrl",
                "rf_notch": "rfnotch_ctrl",
                "dab_notch": "dabnotch_ctrl",
                "if_mode": "if_mode",
                "external_reference": "extref_ctrl",
            }
        )
        return mappings

    def getDriver(self):
        return "sdrplay"


class IfModeOptions(DropdownEnum):
    IFMODE_ZERO_IF = "Zero-IF"
    IFMODE_450 = "450kHz"
    IFMODE_1620 = "1620kHz"
    IFMODE_2048 = "2048kHz"

    def __str__(self):
        return self.value


class SdrplayDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "SDRPlay device (RSP1, RSP2, RSPDuo, RSPDx)"

    def getGainStages(self):
        return ["RFGR", "IFGR"]

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            BiasTeeInput(),
            CheckboxInput(
                "rf_notch",
                "Enable RF notch filter",
            ),
            CheckboxInput(
                "dab_notch",
                "Enable DAB notch filter",
            ),
            DropdownInput(
                "if_mode",
                "IF Mode",
                IfModeOptions,
            ),
        ]

    def getDeviceOptionalKeys(self):
        return super().getDeviceOptionalKeys() + ["bias_tee", "rf_notch", "dab_notch", "if_mode"]

    def getProfileOptionalKeys(self):
        return super().getProfileOptionalKeys() + ["bias_tee", "rf_notch", "dab_notch", "if_mode"]

    def getSampleRateRanges(self) -> list[Range]:
        # this is from SoapySDRPlay3's implementation of listSampleRates().
        # i don't think it's accurate, but this is the limitation we'd be running into if we had proper soapy
        # integration.
        return [
            Range(62500),
            Range(96000),
            Range(125000),
            Range(192000),
            Range(250000),
            Range(384000),
            Range(500000),
            Range(768000),
            Range(1000000),
            Range(2000000),
            Range(2048000),
            Range(3000000),
            Range(4000000),
            Range(5000000),
            Range(6000000),
            Range(7000000),
            Range(8000000),
            Range(9000000),
            Range(10000000),
        ]
