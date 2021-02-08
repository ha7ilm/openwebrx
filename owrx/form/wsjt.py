from owrx.form import Input
from owrx.wsjt import Q65Mode, Q65Interval


class Q65ModeMatrix(Input):
    def checkbox_id(self, mode, interval):
        return "{0}-{1}-{2}".format(self.id, mode.value, interval.value)

    def render_checkbox(self, mode: Q65Mode, interval: Q65Interval, value):
        return """
            <div class="{classes}">
                <input class="form-check-input" type="checkbox" id="{id}" name="{id}" {checked} {disabled}>
                <label class="form-check-label" for="{id}">
                    {checkboxText}
                </label>
            </div>
        """.format(
            classes=self.input_classes(),
            id=self.checkbox_id(mode, interval),
            checked="checked" if "{}{}".format(mode.name, interval.value) in value else "",
            checkboxText="Mode {} interval {}s".format(mode.name, interval.value),
            disabled="" if interval.is_available(mode) else "disabled",
        )

    def render_input(self, value):
        checkboxes = "".join(
            self.render_checkbox(mode, interval, value) for interval in Q65Interval for mode in Q65Mode
        )
        return """
            <div class="matrix q65-matrix">
                {checkboxes}
            </div>
        """.format(
            checkboxes=checkboxes
        )

    def input_classes(self):
        return " ".join(["form-check", "form-control-sm"])

    def parse(self, data):
        def in_response(mode, interval):
            boxid = self.checkbox_id(mode, interval)
            return boxid in data and data[boxid][0] == "on"

        return {
            self.id: [
                "{}{}".format(mode.name, interval.value)
                for interval in Q65Interval
                for mode in Q65Mode
                if in_response(mode, interval)
            ],
        }
