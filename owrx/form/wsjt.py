from owrx.form import Input
from owrx.form.converter import JsonConverter
from owrx.wsjt import Q65Mode, Q65Interval
from owrx.modes import Modes, WsjtMode
import html


class Q65ModeMatrix(Input):
    def checkbox_id(self, mode, interval):
        return "{0}-{1}-{2}".format(self.id, mode.value, interval.value)

    def render_checkbox(self, mode: Q65Mode, interval: Q65Interval, value, errors):
        return """
            <div class="{classes}">
                <input class="form-check-input" type="checkbox" id="{id}" name="{id}" {checked} {disabled}>
                <label class="form-check-label" for="{id}">
                    {checkboxText}
                </label>
            </div>
        """.format(
            classes=self.input_classes(errors),
            id=self.checkbox_id(mode, interval),
            checked="checked" if "{}{}".format(mode.name, interval.value) in value else "",
            checkboxText="Mode {} interval {}s".format(mode.name, interval.value),
            disabled="" if interval.is_available(mode) and not self.disabled else "disabled",
        )

    def render_input_group(self, value, errors):
        return """
            <div class="matrix q65-matrix">
                {checkboxes}
                {errors}
            </div>
        """.format(
            checkboxes=self.render_input(value, errors),
            errors=self.render_errors(errors),
        )

    def render_input(self, value, errors):
        return "".join(
            self.render_checkbox(mode, interval, value, errors) for interval in Q65Interval for mode in Q65Mode
        )

    def input_classes(self, error):
        classes = ["form-check", "form-control-sm"]
        if error:
            classes.append("is-invalid")
        return " ".join(classes)

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
    def defaultConverter(self):
        return JsonConverter()

    def render_input(self, value, errors):
        def render_mode(m):
            return """
                <option value={mode}>{name}</option>
            """.format(
                mode=m.modulation,
                name=m.name,
            )

        return """
            <input type="hidden" class="{classes}" id="{id}" name="{id}" value="{value}" {disabled}>
            <div class="inputs" style="display:none;">
                <select class="form-control form-control-sm">{options}</select>
                <input class="form-control form-control-sm" type="number" step="1">
            </div>
        """.format(
            id=self.id,
            classes=self.input_classes(errors),
            value=html.escape(value),
            options="".join(render_mode(m) for m in Modes.getAvailableModes() if isinstance(m, WsjtMode)),
            disabled="disabled" if self.disabled else ""
        )

    def input_classes(self, error):
        return super().input_classes(error) + " wsjt-decoding-depths"
