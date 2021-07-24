from pycsdr.modules import Buffer, Writer


class Chain:
    def __init__(self, *workers):
        self.input = None
        self.output = None
        self.reader = None
        self.workers = list(workers)
        filtered = self._filterWorkers()
        for i in range(1, len(filtered)):
            self._connect(filtered[i - 1], filtered[i])

    def _filterWorkers(self):
        return [w for w in self.workers if not isinstance(w, Chain) or not w.empty()]

    def empty(self):
        return len(self.workers) <= 0

    def _connect(self, w1, w2):
        writer = Buffer(w1.getOutputFormat())
        w1.setWriter(writer)
        if isinstance(w2, Chain):
            w2.setInput(writer)
        else:
            w2.setReader(writer.getReader())

    def stop(self):
        for w in self.workers:
            w.stop()
        if self.reader is not None:
            self.reader.stop()
            self.reader = None

    def setInput(self, buffer: Buffer):
        if self.input == buffer:
            return
        self.input = buffer
        if self.workers:
            firstWorker = self.workers[0]
            if isinstance(firstWorker, Chain):
                firstWorker.setInput(buffer)
            else:
                firstWorker.setReader(buffer.getReader())
        else:
            self.output = self.input

    def setWriter(self, writer: Writer):
        if self.output == writer:
            return
        self.output = writer
        if self.workers:
            lastWorker = self.workers[-1]
            lastWorker.setWriter(self.output)
        else:
            raise BufferError("setOutput on empty chain")

    def getOutputFormat(self):
        if self.workers:
            return self.workers[-1].getOutputFormat()
        else:
            raise BufferError("getOutputFormat on empty chain")

    def replace(self, index, newWorker):
        if index >= len(self.workers):
            raise IndexError("Index {} does not exist".format(index))

        self.workers[index].stop()
        self.workers[index] = newWorker

        if index == 0:
            writer = self.input
        else:
            previousWorker = self.workers[index - 1]
            writer = Buffer(previousWorker.getOutputFormat())
            previousWorker.setWriter(writer)

        if writer is not None:
            if isinstance(newWorker, Chain):
                newWorker.setInput(writer)
            else:
                newWorker.setReader(writer.getReader())

        if index < len(self.workers) - 1:
            nextWorker = self.workers[index + 1]
            writer = Buffer(newWorker.getOutputFormat())
            newWorker.setWriter(writer)
            if isinstance(nextWorker, Chain):
                nextWorker.setInput(writer)
            else:
                nextWorker.setReader(writer.getReader())
        else:
            if self.output is not None:
                newWorker.setWriter(self.output)

    def pump(self, write):
        if self.output is None:
            self.setWriter(Buffer(self.getOutputFormat()))
        self.reader = self.output.getReader()

        def copy():
            run = True
            while run:
                data = None
                try:
                    data = self.reader.read()
                except ValueError:
                    pass
                if data is None or (isinstance(data, bytes) and len(data) == 0):
                    run = False
                else:
                    write(data)

        return copy

