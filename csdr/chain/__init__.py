class Chain(object):
    def __init__(self, *workers):
        self.workers = workers
        stage = None
        for w in self.workers:
            if stage is not None:
                w.setInput(stage.getBuffer())
            stage = w
        self.buffer = stage.getBuffer()

    def stop(self):
        for w in self.workers:
            w.stop()

    def setInput(self, buffer):
        self.workers[0].setInput(buffer)

    def getBuffer(self):
        return self.buffer
