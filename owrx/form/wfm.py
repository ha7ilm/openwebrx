from owrx.form import DropdownEnum


class WfmTauValues(DropdownEnum):
    TAU_50_MICRO = (50e-6, "most regions")
    TAU_75_MICRO = (75e-6, "Americas and South Korea")

    def __new__(cls, *args, **kwargs):
        value, description = args
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj

    def __str__(self):
        return "{}µs ({})".format(int(self.value * 1e6), self.description)
