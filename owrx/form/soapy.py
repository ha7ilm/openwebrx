from owrx.form import FloatInput


class SoapyGainInput(FloatInput):
    def __init__(self, id, label, gain_stages):
        super().__init__(id, label)
        self.gain_stages = gain_stages

    def render_input(self, value):
        if not self.gain_stages:
            return super().render_input(value)
        # TODO implement input for multiple gain stages here
        return "soapy gain stages here..."
