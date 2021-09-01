import pycsdr.modules


class Module(pycsdr.modules.Module):
    def __init__(self):
        self.reader = None
        self.writer = None
        super().__init__()

    def setReader(self, reader: pycsdr.modules.Reader) -> None:
        self.reader = reader

    def setWriter(self, writer: pycsdr.modules.Writer) -> None:
        self.writer = writer
