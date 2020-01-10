from owrx.parser import Parser


class PocsagParser(Parser):
    def parse(self, raw):
        fields = raw.decode("ascii", "replace").rstrip("\n").split(";")
        meta = {v[0]: "".join(v[1:]) for v in map(lambda x: x.split(":"), fields) if v[0] != ""}
        if "address" in meta:
            meta["address"] = int(meta["address"])
        self.handler.write_pocsag_data(meta)
