class MetaParser(object):
    def __init__(self, handler):
        self.handler = handler
    def parse(self, meta):
        fields = meta.split(";")
        dict = {v[0] : "".join(v[1:]) for v in map(lambda x: x.split(":"), fields)}
        self.handler.write_metadata(dict)