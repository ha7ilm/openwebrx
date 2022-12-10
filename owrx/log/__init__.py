import threading
import os
from logging import Logger, Handler, LogRecord, Formatter


class LogPipe(threading.Thread):

    def __init__(self, level: int, logger: Logger, prefix: str = ""):
        threading.Thread.__init__(self)
        self.daemon = False
        self.level = level
        self.logger = logger
        self.prefix = prefix
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def fileno(self):
        return self.fdWrite

    def run(self):
        for line in iter(self.pipeReader.readline, ''):
            self.logger.log(self.level, "{}: {}".format(self.prefix, line.strip('\n')))

        self.pipeReader.close()

    def close(self):
        os.close(self.fdWrite)


class HistoryHandler(Handler):
    handlers = {}

    @staticmethod
    def getHandler(name: str):
        if name not in HistoryHandler.handlers:
            HistoryHandler.handlers[name] = HistoryHandler()
        return HistoryHandler.handlers[name]

    def __init__(self, maxRecords: int = 200):
        super().__init__()
        self.history = []
        self.maxRecords = maxRecords
        self.setFormatter(Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    def emit(self, record: LogRecord) -> None:
        self.history.append(record)
        # truncate
        self.history = self.history[-self.maxRecords:]

    def getFormattedHistory(self) -> str:
        return "\n".join([self.format(r) for r in self.history])
