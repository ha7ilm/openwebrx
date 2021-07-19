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
        if isinstance(w1, Chain):
            buffer = w1.getOutput()
        else:
            buffer = Buffer(w1.getOutputFormat())
            w1.setOutput(buffer)
        w2.setInput(buffer)

    def stop(self):
        for w in self.workers:
            w.stop()
        self.setInput(None)
        if self.output is not None:
            self.output.stop()

    def setInput(self, buffer):
        if self.input == buffer:
            return
        self.input = buffer
        if self.workers:
            self.workers[0].setInput(buffer)
        else:
            self.output = self.input

    def getOutput(self):
        if self.output is None:
            if self.workers:
                lastWorker = self.workers[-1]
                if isinstance(lastWorker, Chain):
                    self.output = lastWorker.getOutput()
                else:
                    self.output = Buffer(self.getOutputFormat())
                    self.workers[-1].setOutput(self.output)
            else:
                self.output = self.input
        return self.output

    def getOutputFormat(self):
        if self.workers:
            return self.workers[-1].getOutputFormat()
        else:
            return self.input.getOutputFormat()

    def pump(self, write):
        output = self.getOutput()

        def copy():
            run = True
            while run:
                data = None
                try:
                    data = output.read()
                except ValueError:
                    pass
                if data is None or (isinstance(data, bytes) and len(data) == 0):
                    run = False
                else:
                    write(data)

        return copy

