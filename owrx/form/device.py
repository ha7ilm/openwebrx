from owrx.form import Input, CheckboxInput, DropdownInput, DropdownEnum
from owrx.form.converter import OptionalConverter, EnumConverter
from owrx.soapy import SoapySettings


class GainInput(Input):
    def __init__(self, id, label, gain_stages=None):
        super().__init__(id, label)
        self.gain_stages = gain_stages

    def render_input(self, value):
        try:
            display_value = float(value)
        except (ValueError, TypeError):
            display_value = "0.0"

        return """
            <div id="{id}">
                <select class="{classes}" id="{id}-select" name="{id}-select">
                    {options}
                </select>
                <div class="option manual" style="display: none;">
                    <input type="number" id="{id}-manual" name="{id}-manual" value="{value}" class="{classes}"
                    placeholder="Manual device gain" step="any">
                </div>
                {stageoption}
            </div>
        """.format(
            id=self.id,
            classes=self.input_classes(),
            value=display_value,
            label=self.label,
            options=self.render_options(value),
            stageoption="" if self.gain_stages is None else self.render_stage_option(value),
        )

    def render_options(self, value):
        options = [
            ("auto", "Enable hardware AGC"),
            ("manual", "Specify manual gain"),
        ]
        if self.gain_stages:
            options.append(("stages", "Specify gain stages individually"))

        mode = self.getMode(value)

        return "".join(
            """
                <option value="{value}" {selected}>{text}</option>
            """.format(
                value=v[0], text=v[1], selected="selected" if mode == v[0] else ""
            )
            for v in options
        )

    def getMode(self, value):
        if value is None or value == "auto":
            return "auto"

        try:
            float(value)
            return "manual"
        except (ValueError, TypeError):
            pass

        return "stages"

    def render_stage_option(self, value):
        try:
            value_dict = {k: v for item in SoapySettings.parse(value) for k, v in item.items()}
        except (AttributeError, ValueError):
            value_dict = {}

        return """
            <div class="option stages container container-fluid" style="display: none;">
                {inputs}
            </div>
        """.format(
            inputs="".join(
                """
                    <div class="row">
                        <div class="col-3">{stage}</div>
                        <input type="number" id="{id}-{stage}" name="{id}-{stage}" value="{value}"
                        class="col-9 {classes}" placeholder="{stage}" step="any">
                    </div>
                """.format(
                    id=self.id,
                    stage=stage,
                    value=value_dict[stage] if stage in value_dict else "",
                    classes=self.input_classes(),
                )
                for stage in self.gain_stages
            )
        )

    def parse(self, data):
        def getStageValue(stage):
            input_id = "{id}-{stage}".format(id=self.id, stage=stage)
            if input_id in data:
                return data[input_id][0]
            else:
                return None

        select_id = "{id}-select".format(id=self.id)
        if select_id in data:
            if data[select_id][0] == "manual":
                input_id = "{id}-manual".format(id=self.id)
                value = 0.0
                if input_id in data:
                    try:
                        value = float(data[input_id][0])
                    except ValueError:
                        pass
                return {self.id: value}
            if self.gain_stages is not None and data[select_id][0] == "stages":
                settings_dict = [{s: getStageValue(s)} for s in self.gain_stages]
                # filter out empty ones
                settings_dict = [s for s in settings_dict if next(iter(s.values()))]
                return {self.id: SoapySettings.encode(settings_dict)}

        return {self.id: None}


class BiasTeeInput(CheckboxInput):
    def __init__(self):
        super().__init__(
            "bias_tee", "", "Enable Bias-Tee power supply", converter=OptionalConverter(defaultFormValue=False)
        )


class DirectSamplingOptions(DropdownEnum):
    DIRECT_SAMPLING_OFF = (0, "Off")
    DIRECT_SAMPLING_I = (1, "Direct Sampling (I branch)")
    DIRECT_SAMPLING_Q = (2, "Direct Sampling (Q branch)")

    def __new__(cls, *args, **kwargs):
        value, description = args
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj

    def __str__(self):
        return self.description


class DirectSamplingInput(DropdownInput):
    def __init__(self):
        super().__init__(
            "direct_sampling",
            "Direct Sampling",
            DirectSamplingOptions,
            converter=OptionalConverter(
                EnumConverter(DirectSamplingOptions),
                defaultFormValue=DirectSamplingOptions.DIRECT_SAMPLING_OFF.name,
            ),
        )
