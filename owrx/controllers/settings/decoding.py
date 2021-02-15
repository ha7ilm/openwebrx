from owrx.controllers.settings import SettingsFormController, Section
from owrx.form import CheckboxInput, NumberInput, DropdownInput, Js8ProfileCheckboxInput, MultiCheckboxInput, Option
from owrx.form.wfm import WfmTauValues
from owrx.form.wsjt import Q65ModeMatrix, WsjtDecodingDepthsInput
from owrx.wsjt import Fst4Profile, Fst4wProfile


class DecodingSettingsController(SettingsFormController):
    def getTitle(self):
        return "Demodulation and decoding"

    def getSections(self):
        return [
            Section(
                "Demodulator settings",
                NumberInput(
                    "squelch_auto_margin",
                    "Auto-Squelch threshold",
                    infotext="Offset to be added to the current signal level when using the auto-squelch",
                    append="dB",
                ),
                DropdownInput(
                    "wfm_deemphasis_tau",
                    "Tau setting for WFM (broadcast FM) deemphasis",
                    WfmTauValues,
                    infotext='See <a href="https://en.wikipedia.org/wiki/FM_broadcasting#Pre-emphasis_and_de-emphasis">'
                             + "this Wikipedia article</a> for more information",
                ),
            ),
            Section(
                "Digital voice",
                NumberInput(
                    "digital_voice_unvoiced_quality",
                    "Quality of unvoiced sounds in synthesized voice",
                    infotext="Determines the quality, and thus the cpu usage, for the ambe codec used by digital voice"
                             + "modes.<br />If you're running on a Raspi (up to 3B+) you should leave this set at 1",
                ),
                CheckboxInput(
                    "digital_voice_dmr_id_lookup",
                    "DMR id lookup",
                    checkboxText="Enable lookup of DMR ids in the radioid database to show callsigns and names",
                ),
            ),
            Section(
                "Digimodes",
                CheckboxInput("digimodes_enable", "", checkboxText="Enable Digimodes"),
                NumberInput("digimodes_fft_size", "Digimodes FFT size", append="bins"),
            ),
            Section(
                "Decoding settings",
                NumberInput("decoding_queue_workers", "Number of decoding workers"),
                NumberInput("decoding_queue_length", "Maximum length of decoding job queue"),
                NumberInput(
                    "wsjt_decoding_depth",
                    "Default WSJT decoding depth",
                    infotext="A higher decoding depth will allow more results, but will also consume more cpu",
                ),
                WsjtDecodingDepthsInput(
                    "wsjt_decoding_depths",
                    "Individual decoding depths",
                ),
                NumberInput(
                    "js8_decoding_depth",
                    "Js8Call decoding depth",
                    infotext="A higher decoding depth will allow more results, but will also consume more cpu",
                ),
                Js8ProfileCheckboxInput("js8_enabled_profiles", "Js8Call enabled modes"),
                MultiCheckboxInput(
                    "fst4_enabled_intervals",
                    "Enabled FST4 intervals",
                    [Option(v, "{}s".format(v)) for v in Fst4Profile.availableIntervals],
                ),
                MultiCheckboxInput(
                    "fst4w_enabled_intervals",
                    "Enabled FST4W intervals",
                    [Option(v, "{}s".format(v)) for v in Fst4wProfile.availableIntervals],
                ),
                Q65ModeMatrix("q65_enabled_combinations", "Enabled Q65 Mode combinations"),
            ),
        ]
