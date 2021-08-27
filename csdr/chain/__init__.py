from pycsdr.modules import Buffer
from typing import Union, Callable


class Chain:
    def __init__(self, workers):
        self.reader = None
        self.writer = None
        self.clientReader = None
        self.workers = workers
        for i in range(1, len(self.workers)):
            self._connect(self.workers[i - 1], self.workers[i])

    def empty(self):
        return not self.workers

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

    def indexOf(self, search: Union[Callable, object]) -> int:
        def searchFn(x):
            if callable(search):
                return search(x)
            else:
                return x is search

        try:
            return next(i for i, v in enumerate(self.workers) if searchFn(v))
        except StopIteration:
            return -1

    def replace(self, index, newWorker):
        if index >= len(self.workers):
            raise IndexError("Index {} does not exist".format(index))

        self.workers[index].stop()
        self.workers[index] = newWorker

        error = None

        if index == 0:
            if self.reader is not None:
                newWorker.setReader(self.reader)
        else:
            try:
                previousWorker = self.workers[index - 1]
                self._connect(previousWorker, newWorker)
            except ValueError as e:
                # store error for later raising, but still attempt the second connection
                error = e

        if index == len(self.workers) - 1:
            if self.writer is not None:
                newWorker.setWriter(self.writer)
        else:
            try:
                nextWorker = self.workers[index + 1]
                self._connect(newWorker, nextWorker)
            except ValueError as e:
                error = e

        if error is not None:
            raise error

    def append(self, newWorker):
        previousWorker = None
        if self.workers:
            previousWorker = self.workers[-1]

        self.workers.append(newWorker)

        if previousWorker:
            self._connect(previousWorker, newWorker)
        elif self.reader is not None:
            newWorker.setReader(self.reader)

        if self.writer is not None:
            newWorker.setWriter(self.writer)

    def insert(self, newWorker):
        nextWorker = None
        if self.workers:
            nextWorker = self.workers[0]

        self.workers.insert(0, newWorker)

        if nextWorker:
            self._connect(newWorker, nextWorker)
        elif self.writer is not None:
            newWorker.setWriter(self.writer)

        if self.reader is not None:
            newWorker.setReader(self.reader)

    def remove(self, index):
        removedWorker = self.workers[index]
        self.workers.remove(removedWorker)
        removedWorker.stop()

        if index == 0:
            if self.reader is not None:
                self.workers[0].setReader(self.reader)
        elif index == len(self.workers):
            if self.writer is not None:
                self.workers[-1].setWriter(self.writer)
        else:
            previousWorker = self.workers[index - 1]
            nextWorker = self.workers[index]
            self._connect(previousWorker, nextWorker)

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
