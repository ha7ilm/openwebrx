import os
import select
import time
import threading

import logging

logger = logging.getLogger(__name__)


class Pipe(object):
    READ = "r"
    WRITE = "w"
    NONE = None

    @staticmethod
    def create(path, t, encoding=None):
        if t == Pipe.READ:
            return ReadingPipe(path, encoding=encoding)
        elif t == Pipe.WRITE:
            return WritingPipe(path, encoding=encoding)
        elif t == Pipe.NONE:
            return Pipe(path, None, encoding=encoding)

    def __init__(self, path, direction, encoding=None):
        self.doOpen = True
        self.path = "{base}_{myid}".format(base=path, myid=id(self))
        self.direction = direction
        self.encoding = encoding
        self.file = None
        os.mkfifo(self.path)

    def open(self):
        retries = 0

        def opener(path, flags):
            fd = os.open(path, flags | os.O_NONBLOCK)
            os.set_blocking(fd, True)
            return fd

        while self.file is None and self.doOpen and retries < 10:
            try:
                self.file = open(self.path, self.direction, encoding=self.encoding, opener=opener)
            except OSError as error:
                # ENXIO = FIFO has not been opened for reading
                if error.errno == 6:
                    time.sleep(.1)
                    retries += 1
                else:
                    raise

        # if doOpen is false, opening has been canceled, so no warning in that case.
        if self.file is None and self.doOpen:
            logger.warning("could not open FIFO %s", self.path)

    def close(self):
        self.doOpen = False
        try:
            if self.file is not None:
                self.file.close()
            os.unlink(self.path)
        except FileNotFoundError:
            # it seems like we keep calling this twice. no idea why, but we don't need the resulting error.
            pass
        except Exception:
            logger.exception("Pipe.close()")

    def __str__(self):
        return self.path


class WritingPipe(Pipe):
    def __init__(self, path, encoding=None):
        self.queue = []
        self.queueLock = threading.Lock()
        super().__init__(path, "w", encoding=encoding)
        self.open()

    def open_and_dequeue(self):
        super().open()

        if self.file is None:
            return

        with self.queueLock:
            for i in self.queue:
                self.file.write(i)
            self.file.flush()
            self.queue = None

    def open(self):
        threading.Thread(target=self.open_and_dequeue).start()

    def write(self, data):
        if self.file is None:
            with self.queueLock:
                self.queue.append(data)
            return
        r = self.file.write(data)
        self.file.flush()
        return r


class ReadingPipe(Pipe):
    def __init__(self, path, encoding=None):
        super().__init__(path, "r", encoding=encoding)

    def open(self):
        if not self.doOpen:
            return
        super().open()
        select.select([self.file], [], [], 10)

    def read(self):
        if self.file is None:
            self.open()
        return self.file.read()

    def readline(self):
        if self.file is None:
            self.open()
        return self.file.readline()
