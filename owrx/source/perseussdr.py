from owrx.source.direct import DirectSource, DirectSourceDeviceDescription
from owrx.command import Option, Flag
from owrx.form.input import Input, DropdownEnum, DropdownInput, CheckboxInput
from typing import List


#
# In order to interface Perseus hardware, we resolve to use the
# perseustest utility that comes with libperseus-sdr support package.
# Below the base options used are shown:
#
# -p output    I/Q samples as 32 bits floating point
# -d -1        suppress debug messages
# -a           don't test attenuators on startup
# -t 0         runs indefinitely
# -o -         output samples on stdout
#
# As we are already returning I/Q samples as pairs of 32 bits
# floating points (option -p),no need for further conversions,
# so the method getFormatConversion(self) is not implemented at all.


class PerseussdrSource(DirectSource):
    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setBase("perseustest -p -d -1 -a -t 0 -o -  ")
            .setMappings(
                {
                    "samp_rate": Option("-s"),
                    "tuner_freq": Option("-f"),
                    "attenuator": Option("-u"),
                    "adc_preamp": Flag("-m"),
                    "adc_dither": Flag("-x"),
                    "wideband": Flag("-w"),
                }
            )
        )


class AttenuatorOptions(DropdownEnum):
    ATTENUATOR_0 = 0
    ATTENUATOR_10 = -10
    ATTENUATOR_20 = -20
    ATTENUATOR_30 = -30

    def __str__(self):
        return "{value} dB".format(value=self.value)


class PerseussdrDeviceDescription(DirectSourceDeviceDescription):
    def getName(self):
        return "Perseus SDR"

    def supportsPpm(self):
        # not currently mapped, and not available as an option to "perseustest"
        return False

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            DropdownInput("attenuator", "Attenuator", options=AttenuatorOptions),
            CheckboxInput("adc_preamp", "Activate ADC preamp"),
            CheckboxInput("adc_dither", "Enable ADC dithering"),
            CheckboxInput("wideband", "Disable analog filters"),
        ]

    def getDeviceOptionalKeys(self):
        # no rf_gain
        return [key for key in super().getDeviceOptionalKeys() if key != "rf_gain"] + [
            "attenuator",
            "adc_preamp",
            "adc_dither",
            "wideband",
        ]

    def getProfileOptionalKeys(self):
        return [key for key in super().getProfileOptionalKeys() if key != "rf_gain"] + [
            "attenuator",
            "adc_preamp",
            "adc_dither",
            "wideband",
        ]
