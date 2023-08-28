from csdr.module import Module
from pycsdr.modules import Buffer
from pycsdr.types import Format
from typing import Union, Callable, Optional


class Chain(Module):
    def __init__(self, workers):
        super().__init__()
        self.workers = workers
        for i in range(1, len(self.workers)):
            self._connect(self.workers[i - 1], self.workers[i])

    def empty(self):
        return not self.workers

    def _connect(self, w1, w2, buffer: Optional[Buffer] = None) -> None:
        if buffer is None:
            buffer = Buffer(w1.getOutputFormat())
        w1.setWriter(buffer)
        w2.setReader(buffer.getReader())

    def setReader(self, reader):
        if self.reader is reader:
            return
        super().setReader(reader)
        if self.workers:
            self.workers[0].setReader(reader)

    def setWriter(self, writer):
        if self.writer is writer:
            return
        super().setWriter(writer)
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

    def insert(self, index, newWorker):
        nextWorker = None
        previousWorker = None
        if index < len(self.workers):
            nextWorker = self.workers[index]
        if index > 0:
            previousWorker = self.workers[index - 1]

        self.workers.insert(index, newWorker)

        if nextWorker:
            self._connect(newWorker, nextWorker)
        elif self.writer is not None:
            newWorker.setWriter(self.writer)

        if previousWorker:
            self._connect(previousWorker, newWorker)
        elif self.reader is not None:
            newWorker.setReader(self.reader)

    def remove(self, index):
        removedWorker = self.workers[index]
        self.workers.remove(removedWorker)
        removedWorker.stop()

        if index == 0:
            if self.reader is not None and len(self.workers):
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

    def getInputFormat(self) -> Format:
        if self.workers:
            return self.workers[0].getInputFormat()
        else:
            raise BufferError("getInputFormat on empty chain")

    def getOutputFormat(self) -> Format:
        if self.workers:
            return self.workers[-1].getOutputFormat()
        else:
            raise BufferError("getOutputFormat on empty chain")
