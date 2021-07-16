from pycsdr.modules import Buffer

import logging
logger = logging.getLogger(__name__)


class Chain:
    def __init__(self, *workers):
        self.input = None
        self.output = None
        self.workers = workers
        for i in range(1, len(self.workers)):
            self._connect(self.workers[i - 1], self.workers[i])

    def _connect(self, w1, w2):
        buffer = Buffer(w1.getOutputFormat())
        w1.setOutput(buffer)
        w2.setInput(buffer)

    def stop(self):
        if self.output is not None:
            self.output.stop()
        for w in self.workers:
            w.stop()

    def setInput(self, buffer):
        if self.input == buffer:
            return
        self.input = buffer
        self.workers[0].setInput(buffer)

    def setOutput(self, buffer):
        if self.output == buffer:
            return
        self.output = buffer
        self.workers[-1].setOutput(buffer)

    def getOutputFormat(self):
        return self.workers[-1].getOutputFormat()

    def pump(self, write):
        if self.output is None:
            self.setOutput(Buffer(self.getOutputFormat()))

        def copy():
            run = True
            while run:
                data = None
                try:
                    data = self.output.read()
                except ValueError:
                    pass
                if data is None or (isinstance(data, bytes) and len(data) == 0):
                    run = False
                else:
                    write(data)

        return copy

