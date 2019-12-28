from abc import ABC, abstractmethod


class CommandMapper(object):
    def __init__(self, base=None, mappings={}, static=None):
        self.base = base
        self.mappings = mappings
        self.static = static

    def map(self, values):
        args = [self.mappings[k].map(v) for k, v in values.items() if k in self.mappings]
        args = [a for a in args if a != ""]
        options = " ".join(args)
        command = "{0} {1}".format(self.base, options)
        if self.static is not None:
            command += " " + self.static
        return command

    def setMapping(self, key, mapping):
        self.mappings[key] = mapping
        return self

    def setMappings(self, mappings):
        for k, v in mappings.items():
            self.setMapping(k, v)
        return self

    def setBase(self, base):
        self.base = base
        return self

    def setStatic(self, static):
        self.static = static
        return self


class CommandMapping(ABC):
    @abstractmethod
    def map(self, value):
        pass


class Flag(CommandMapping):
    def __init__(self, flag):
        self.flag = flag

    def map(self, value):
        if value is not None and value:
            return self.flag
        else:
            return ""


class Option(CommandMapping):
    def __init__(self, option):
        self.option = option

    def map(self, value):
        if value is not None:
            if isinstance(value, str) and " " in value:
                template = "{0} \"{1}\""
            else:
                template = "{0} {1}"
            return template.format(self.option, value)
        else:
            return ""
