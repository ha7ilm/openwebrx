from owrx.form import Input
from owrx.wsjt import Q65Mode, Q65Interval
from owrx.modes import Modes, WsjtMode
import json
import html


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


class WsjtDecodingDepthsInput(Input):
    def render_input(self, value):
        def render_mode(m):
            return """
                <option value={mode}>{name}</option>
            """.format(
                mode=m.modulation,
                name=m.name,
            )

        return """
            <input type="hidden" class="{classes}" id="{id}" name="{id}" value="{value}">
            <div class="inputs" style="display:none;">
                <select class="form-control form-control-sm">{options}</select>
                <input class="form-control form-control-sm" type="number" step="1">
            </div>
        """.format(
            id=self.id,
            classes=self.input_classes(),
            value=html.escape(json.dumps(value)),
            options="".join(render_mode(m) for m in Modes.getAvailableModes() if isinstance(m, WsjtMode)),
        )

    def input_classes(self):
        return super().input_classes() + " wsjt-decoding-depths"
