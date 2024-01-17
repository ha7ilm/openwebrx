from owrx.form.error import FormError
from owrx.form.input import Input
from typing import List


class Section(object):
    def __init__(self, title, *inputs):
        self.title = title
        self.inputs = inputs

    def render_input(self, input, data, errors):
        return input.render(data, errors)

    def render_inputs(self, data, errors):
        return "".join([self.render_input(i, data, errors) for i in self.inputs])

    def classes(self):
        return ["col-12", "settings-section"]

    def render(self, data, errors):
        return """
            <div class="{classes}">
                <h3 class="settings-header">
                    {title}
                </h3>
                {inputs}
            </div>
        """.format(
            classes=" ".join(self.classes()), title=self.title, inputs=self.render_inputs(data, errors)
        )

    def parse(self, data):
        parsed_data = {}
        errors = []
        for i in self.inputs:
            try:
                res = i.parse(data)
                parsed_data.update(res)
                i.validate(res)
            except FormError as e:
                errors.append(e)
            except Exception as e:
                errors.append(FormError(i.id, "{}: {}".format(type(e).__name__, e)))
        return parsed_data, errors


class OptionalSection(Section):
    def __init__(self, title, inputs: List[Input], mandatory, optional):
        super().__init__(title, *inputs)
        self.mandatory = mandatory
        self.optional = optional
        self.optional_inputs = []

    def classes(self):
        classes = super().classes()
        classes.append("optional-section")
        return classes

    def _is_optional(self, input):
        return input.id in self.optional

    def render_optional_select(self):
        return """
            <hr class="row" />
            <div class="form-group row">
                <label class="col-form-label col-form-label-sm col-3">
                    Additional optional settings
                </label>
                <div class="add-group col-9 p-0">
                    <div class="add-group-select">
                        <select class="form-control form-control-sm optional-select">
                            {options}
                        </select>
                    </div>
                    <button type="button" class="btn btn-sm btn-success option-add-button">Add</button>
                </div>
            </div>
        """.format(
            options="".join(
                """
                    <option value="{value}">{name}</option>
                """.format(
                    value=input.id,
                    name=input.getLabel(),
                )
                for input in self.optional_inputs
            )
        )

    def render_optional_inputs(self, data, errors):
        return """
            <div class="optional-inputs" style="display: none;">
                {inputs}
            </div>
        """.format(
            inputs="".join(self.render_input(input, data, errors) for input in self.optional_inputs)
        )

    def render_inputs(self, data, errors):
        return (
                super().render_inputs(data, errors)
                + self.render_optional_select()
                + self.render_optional_inputs(data, errors)
        )

    def render(self, data, errors):
        indexed_inputs = {input.id: input for input in self.inputs}
        visible_keys = set(self.mandatory + [k for k in self.optional if k in data or k in errors])
        optional_keys = set(k for k in self.optional if k not in data and k not in errors)
        self.inputs = [input for k, input in indexed_inputs.items() if k in visible_keys]
        for input in self.inputs:
            if self._is_optional(input):
                input.setRemovable()
        self.optional_inputs = [input for k, input in indexed_inputs.items() if k in optional_keys]
        for input in self.optional_inputs:
            input.setRemovable()
            input.setDisabled()
        return super().render(data, errors)

    def parse(self, data):
        data, errors = super().parse(data)
        # remove optional keys if they have been removed from the form by setting them to None
        for k in self.optional:
            if k not in data:
                data[k] = None
        return data, errors
