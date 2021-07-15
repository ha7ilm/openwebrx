class SoapySettings(object):
    @staticmethod
    def parse(dstr):
        def decodeComponent(c):
            kv = c.split("=", 1)
            if len(kv) < 2:
                return c
            else:
                return {kv[0]: kv[1]}

        return [decodeComponent(c) for c in dstr.split(",")]

    @staticmethod
    def encode(dobj):
        def encodeComponent(c):
            if isinstance(c, str):
                return c
            else:
                return ",".join(["{0}={1}".format(key, value) for key, value in c.items()])

        return ",".join([encodeComponent(c) for c in dobj])
