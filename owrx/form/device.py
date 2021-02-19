from owrx.form import Input
from owrx.soapy import SoapySettings


class GainInput(Input):
    def __init__(self, id, label, gain_stages=None):
        super().__init__(id, label)
        self.gain_stages = gain_stages

    def render_input(self, value):
        return """
            <div id="{id}">
                <select class="{classes}" id="{id}-select" name="{id}-select">
                    {options}
                </select>
                <div class="option manual" style="display: none;">
                    <input type="number" id="{id}-manual" name="{id}-manual" value="{value}" class="{classes}" placeholder="Manual device gain" step="any">
                </div>
                {stageoption}
            </div>
        """.format(
            id=self.id,
            classes=self.input_classes(),
            value="0.0" if value is None else value,
            label=self.label,
            options=self.render_options(value),
            stageoption=self.render_stage_option(value),
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
                value=v[0],
                text=v[1],
                selected="selected" if mode == v[0] else ""
            )
            for v in options
        )

    def getMode(self, value):
        if value is None or value == "auto":
            return "auto"

        try:
            float(value)
            return "manual"
        except ValueError:
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
                        <input type="number" id="{id}-{stage}" name="{id}-{stage}" value="{value}" class="col-9 {classes}" placeholder="{stage}" step="any">
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
                return 0.0

        select_id = "{id}-select".format(id=self.id)
        if select_id in data:
            if data[select_id][0] == "manual":
                input_id = "{id}-manual".format(id=self.id)
                value = 0.0
                if input_id in data:
                    try:
                        value = float(float(data[input_id][0]))
                    except ValueError:
                        pass
                return {self.id: value}
            if data[select_id][0] == "stages":
                settings_dict = [{s: getStageValue(s)} for s in self.gain_stages]
                return {self.id: SoapySettings.encode(settings_dict)}

        return {self.id: None}
