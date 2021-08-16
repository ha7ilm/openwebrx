from pycsdr.modules import Buffer, Writer


class Chain:
    def __init__(self, *workers):
        self.reader = None
        self.writer = None
        self.clientReader = None
        self.workers = list(workers)
        for i in range(1, len(self.workers)):
            self._connect(self.workers[i - 1], self.workers[i])

    def _connect(self, w1, w2):
        writer = Buffer(w1.getOutputFormat())
        w1.setWriter(writer)
        w2.setReader(writer.getReader())

    def setReader(self, reader):
        if self.reader is reader:
            return
        self.reader = reader
        if self.workers:
            self.workers[0].setReader(reader)

    def setWriter(self, writer):
        if self.writer is writer:
            return
        self.writer = writer
        if self.workers:
            self.workers[-1].setWriter(writer)

    def stop(self):
        for w in self.workers:
            w.stop()
        if self.clientReader is not None:
            # TODO should be covered by finalize
            self.clientReader.stop()
            self.clientReader = None

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
            if self.reader is not None:
                newWorker.setReader(self.reader)
        else:
            previousWorker = self.workers[index - 1]
            buffer = Buffer(previousWorker.getOutputFormat())
            previousWorker.setWriter(buffer)
            newWorker.setReader(buffer.getReader())

        if index == len(self.workers) - 1:
            if self.writer is not None:
                newWorker.setWriter(self.writer)
        else:
            nextWorker = self.workers[index + 1]
            buffer = Buffer(newWorker.getOutputFormat())
            newWorker.setWriter(buffer)
            nextWorker.setReader(buffer.getReader())

    def pump(self, write):
        if self.writer is None:
            self.setWriter(Buffer(self.getOutputFormat()))
        self.clientReader = self.writer.getReader()

        def copy():
            run = True
            while run:
                data = None
                try:
                    data = self.clientReader.read()
                except ValueError:
                    pass
                if data is None:
                    run = False
                else:
                    write(data)

        return copy

