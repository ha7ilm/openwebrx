from owrx.form.input import Input, CheckboxInput, DropdownInput, DropdownEnum, TextInput
from owrx.form.input.converter import OptionalConverter
from owrx.form.input.validator import RequiredValidator
from owrx.soapy import SoapySettings


class GainInput(Input):
    def __init__(self, id, label, has_agc, gain_stages=None):
        super().__init__(id, label)
        self.has_agc = has_agc
        self.gain_stages = gain_stages

    def render_input(self, value, errors):
        try:
            display_value = float(value)
        except (ValueError, TypeError):
            display_value = "0.0"

        return """
            <select class="{classes}" id="{id}-select" name="{id}-select" {disabled}>
                {options}
            </select>
            <div class="option manual" style="display: none;">
                <input type="number" id="{id}-manual" name="{id}-manual" value="{value}" class="{classes}"
                placeholder="Manual device gain" step="any" {disabled}>
            </div>
            {stageoption}
        """.format(
            id=self.id,
            classes=self.input_classes(errors),
            value=display_value,
            label=self.label,
            options=self.render_options(value),
            stageoption="" if self.gain_stages is None else self.render_stage_option(value, errors),
            disabled="disabled" if self.disabled else "",
        )

    def render_input_group(self, value, errors):
        return """
            <div id="{id}">
                {input}
                {errors}
            </div>
        """.format(
            id=self.id, input=self.render_input(value, errors), errors=self.render_errors(errors)
        )

    def render_options(self, value):
        options = []
        if self.has_agc:
            options.append(("auto", "Enable hardware AGC"))
        options.append(("manual", "Specify manual gain")),
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
        if value is None:
            return "auto" if self.has_agc else "manual"

        if value == "auto":
            return "auto"

        try:
            float(value)
            return "manual"
        except (ValueError, TypeError):
            pass

        return "stages"

    def render_stage_option(self, value, errors):
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
                        <label class="col-form-label col-form-label-sm col-3">{stage}</label>
                        <input type="number" id="{id}-{stage}" name="{id}-{stage}" value="{value}"
                        class="col-9 {classes}" placeholder="{stage}" step="any" {disabled}>
                    </div>
                """.format(
                    id=self.id,
                    stage=stage,
                    value=value_dict[stage] if stage in value_dict else "",
                    classes=self.input_classes(errors),
                    disabled="disabled" if self.disabled else "",
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
            if self.has_agc and data[select_id][0] == "auto":
                return {self.id: "auto"}
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

        return {}


class BiasTeeInput(CheckboxInput):
    def __init__(self):
        super().__init__("bias_tee", "Enable Bias-Tee power supply")


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
        )


class RemoteInput(TextInput):
    def __init__(self):
        super().__init__(
            "remote",
            "Remote IP and Port",
            infotext="Remote hostname or IP and port to connect to. Format = IP:Port",
            converter=OptionalConverter(),
            validator=RequiredValidator(),
        )


class SchedulerInput(Input):
    def __init__(self, id, label):
        super().__init__(id, label)
        self.profiles = {}

    def render(self, config, errors):
        if "profiles" in config:
            self.profiles = config["profiles"]
        return super().render(config, errors)

    def render_profiles_select(self, value, errors, config_key, stage, extra_classes="", allow_empty=False):
        stage_value = ""
        if value and "schedule" in value and config_key in value["schedule"]:
            stage_value = value["schedule"][config_key]

        options = "".join(
            """
                <option value="{id}" {selected}>{name}</option>
            """.format(
                id=p_id,
                name=p["name"],
                selected="selected" if stage_value == p_id else "",
            )
            for p_id, p in self.profiles.items()
        )

        if allow_empty:
            # prepend a special "off" option to allow a schedule slot to go unused (daylight scheduler)
            options = """<option value="None" {selected}>Off</option>""".format(
                selected="selected" if value is None else ""
            ) + options

        return """
            <select class="{extra_classes} {classes}" id="{id}" name="{id}" {disabled}>
                {options}
            </select> 
        """.format(
            id="{}-{}".format(self.id, stage),
            classes=self.input_classes(errors),
            extra_classes=extra_classes,
            disabled="disabled" if self.disabled else "",
            options=options,
        )

    def render_static_entires(self, value, errors):
        def render_time_inputs(v):
            values = ["{}:{}".format(x[0:2], x[2:4]) for x in [v[0:4], v[5:9]]]
            return '<div class="p-1">-</div>'.join(
                """
                    <input type="time" class="{classes}" id="{id}" name="{id}" {disabled} value="{value}">
                """.format(
                    id="{}-{}-{}".format(self.id, "time", "start" if i == 0 else "end"),
                    classes=self.input_classes(errors),
                    disabled="disabled" if self.disabled else "",
                    value=v,
                )
                for i, v in enumerate(values)
            )

        schedule = {"0000-0000": ""}
        if value is not None and value and "schedule" in value and "type" in value and value["type"] == "static":
            schedule = value["schedule"]

        rows = "".join(
            """
                <div class="row scheduler-static-time-inputs">
                    {time_inputs}
                    {select}
                    <button type="button" class="btn btn-sm btn-danger remove-button">X</button>
                </div>
            """.format(
                time_inputs=render_time_inputs(slot),
                select=self.render_profiles_select(value, errors, slot, "profile"),
            )
            for slot, entry in schedule.items()
        )

        return """
            {rows}
            <div class="row scheduler-static-time-inputs template" style="display: none;">
                {time_inputs}
                {select}
                <button type="button" class="btn btn-sm btn-danger remove-button">X</button>
            </div>
            <div class="row">
                <button type="button" class="btn btn-sm btn-primary col-12 add-button">Add...</button>
            </div>
        """.format(
            rows=rows,
            time_inputs=render_time_inputs("0000-0000"),
            select=self.render_profiles_select("", errors, "0000-0000", "profile"),
        )

    def render_daylight_entries(self, value, errors):
        return "".join(
            """
                <div class="row">
                    <label class="col-form-label col-form-label-sm col-3">{name}</label>
                    {select}
                </div>
            """.format(
                name=name,
                select=self.render_profiles_select(
                    value, errors, stage, stage, extra_classes="col-9", allow_empty=True
                ),
            )
            for stage, name in [("day", "Day"), ("night", "Night"), ("greyline", "Greyline")]
        )

    def render_input(self, value, errors):
        return """
            <div id="{id}">
                <select class="{classes} mode" id="{id}-select" name="{id}-select" {disabled}>
                    {options}
                </select>
                <div class="option static container container-fluid" style="display: none;">
                    {entries}
                </div>
                <div class="option daylight container container-fluid" style="display: None;">
                    {stages}
                </div>
            </div>
        """.format(
            id=self.id,
            classes=self.input_classes(errors),
            disabled="disabled" if self.disabled else "",
            options=self.render_options(value),
            entries=self.render_static_entires(value, errors),
            stages=self.render_daylight_entries(value, errors),
        )

    def _get_mode(self, value):
        if value is not None and "type" in value:
            return value["type"]
        return ""

    def render_options(self, value):
        options = [
            ("static", "Static scheduler"),
            ("daylight", "Daylight scheduler"),
        ]

        mode = self._get_mode(value)

        return "".join(
            """
                <option value="{value}" {selected}>{name}</option>
            """.format(
                value=value, name=name, selected="selected" if mode == value else ""
            )
            for value, name in options
        )

    def parse(self, data):
        def getStageValue(stage):
            input_id = "{id}-{stage}".format(id=self.id, stage=stage)
            if input_id in data:
                # special treatment for the "off" option
                if data[input_id][0] == "None":
                    return None
                return data[input_id][0]
            else:
                return None

        select_id = "{id}-select".format(id=self.id)
        if select_id in data:
            if data[select_id][0] == "static":
                keys = ["{}-{}".format(self.id, x) for x in ["time-start", "time-end", "profile"]]
                lists = [data[key] for key in keys if key in data]
                settings_dict = {
                    "{}{}-{}{}".format(start[0:2], start[3:5], end[0:2], end[3:5]): profile
                    for start, end, profile in zip(*lists)
                }
                # only apply scheduler if any slots are available
                if settings_dict:
                    return {self.id: {"type": "static", "schedule": settings_dict}}
            elif data[select_id][0] == "daylight":
                settings_dict = {s: getStageValue(s) for s in ["day", "night", "greyline"]}
                # filter out empty ones
                settings_dict = {s: v for s, v in settings_dict.items() if v}
                # only apply scheduler if any of the slots are in use
                if settings_dict:
                    return {self.id: {"type": "daylight", "schedule": settings_dict}}

        return {}


class WaterfallLevelsInput(Input):
    def __init__(self, id, label, infotext=None):
        super().__init__(id, label, infotext=infotext)

    def render_input_group(self, value, errors):
        return """
            <div class="row {rowclass}" id="{id}">
                {input}
            </div>
            {errors}
        """.format(
            rowclass="is-invalid" if errors else "",
            id=self.id,
            input=self.render_input(value, errors),
            errors=self.render_errors(errors),
        )

    def getUnit(self):
        return "dBFS"

    def getFields(self):
        return {"min": "Minimum", "max": "Maximum"}

    def render_input(self, value, errors):
        return "".join(
            """
                <div class="col row">
                    <label class="col-3 col-form-label col-form-label-sm" for="{id}-{name}">{label}</label>
                    <div class="col-9 input-group input-group-sm">
                        <input type="number" step="any" class="{classes}" name="{id}-{name}" value="{value}" {disabled}>
                        <div class="input-group-append">
                            <span class="input-group-text">{unit}</span>
                        </div>
                    </div>
                </div>
            """.format(
                id=self.id,
                name=name,
                label=label,
                value=value[name] if value and name in value else "0",
                classes=self.input_classes(errors),
                disabled="disabled" if self.disabled else "",
                unit=self.getUnit(),
            )
            for name, label in self.getFields().items()
        )

    def parse(self, data):
        def getValue(name):
            key = "{}-{}".format(self.id, name)
            if key in data:
                return {name: float(data[key][0])}
            raise KeyError("waterfall key not found")

        try:
            return {self.id: {k: v for name in ["min", "max"] for k, v in getValue(name).items()}}
        except KeyError:
            return {}


class WaterfallAutoLevelsInput(WaterfallLevelsInput):
    def getUnit(self):
        return "dB"

    def getFields(self):
        return {"min": "Lower", "max": "Upper"}
