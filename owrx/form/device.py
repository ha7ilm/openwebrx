from owrx.form import Input


class GainInput(Input):
    def render_input(self, value):
        auto_mode = value is None or value == "auto"

        return """
            <div id="{id}">
                <select class="{classes}" id="{id}-select" name="{id}-select">
                    <option value="auto" {auto_selected}>Enable hardware AGC</option>
                    <option value="manual" {manual_selected}>Specify manual gain</option>
                </select>
                <div class="option manual" style="display: none;">
                    <input type="number" id="{id}-manual" name="{id}-manual" value="{value}" class="{classes}" placeholder="Manual device gain" value="{value}" step="any">
                </div>
            </div>
        """.format(
            id=self.id,
            classes=self.input_classes(),
            value=value,
            label=self.label,
            auto_selected="selected" if auto_mode else "",
            manual_selected="" if auto_mode else "selected",
        )

    def parse(self, data):
        select_id = "{id}-select".format(id=self.id)
        if select_id in data:
            input_id = "{id}-manual".format(id=self.id)
            if data[select_id][0] == "manual" and input_id in data:
                return {self.id: float(data[input_id][0])}
        return {self.id: None}
