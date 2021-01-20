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
        """
        this method opens the file descriptor with an added O_NONBLOCK flag. This gives us a special behaviour for
        FIFOS, when they are not opened by the opposing side:

         - opening a pipe for writing will throw an OSError with errno = 6 (ENXIO). This is handled specially in the
           WritingPipe class.
         - opening a pipe for reading will pass through this method instantly, even if the opposing end has not been
           opened yet, but the resulting file descriptor will behave as if O_NONBLOCK is set (even if we remove it
           immediately here), resulting in empty reads until data is available. This is handled specially in the
           ReadingPipe class.
        """

        def opener(path, flags):
            fd = os.open(path, flags | os.O_NONBLOCK)
            os.set_blocking(fd, True)
            return fd

        self.file = open(self.path, self.direction, encoding=self.encoding, opener=opener)

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
        """
        This method implements a retry loop that can be interrupted in case the Pipe gets shutdown before actually
        being connected.

        After the pipe is opened successfully, all data that has been queued is sent in the order it was passed into
        write().
        """
        retries = 0

        while self.file is None and self.doOpen and retries < 10:
            try:
                super().open()
            except OSError as error:
                # ENXIO = FIFO has not been opened for reading
                if error.errno == 6:
                    time.sleep(0.1)
                    retries += 1
                else:
                    raise

        # if doOpen is false, opening has been canceled, so no warning in that case.
        if self.file is None:
            if self.doOpen:
                logger.warning("could not open FIFO %s", self.path)
            return

        with self.queueLock:
            for i in self.queue:
                self.file.write(i)
            self.file.flush()
            self.queue = None

    def open(self):
        """
        This sends the opening operation off to a background thread. If we were to block the thread here, another pipe
        may be waiting in the queue to be opened on the opposing side, resulting in a deadlock
        """
        threading.Thread(target=self.open_and_dequeue, name="csdr_pipe_thread").start()

    def write(self, data):
        """
        This method queues all data to be written until the file is actually opened. As soon as a file is available,
        it becomes a passthrough.
        """
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
        """
        This method implements an interruptible loop that waits for the file descriptor to be opened and the first
        batch of data coming in using repeated select() calls.
        :return:
        """
        if not self.doOpen:
            return
        super().open()
        while self.doOpen:
            (read, _, _) = select.select([self.file], [], [], 1)
            if self.file in read:
                break

    def read(self):
        if self.file is None:
            self.open()
        return self.file.read()

    def readline(self):
        if self.file is None:
            self.open()
        return self.file.readline()
