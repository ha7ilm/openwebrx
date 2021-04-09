import threading
import logging

logger = logging.getLogger(__name__)


class Output(object):
    def send_output(self, t, read_fn):
        if not self.supports_type(t):
            # TODO rewrite the output mechanism in a way that avoids producing unnecessary data
            logger.warning("dumping output of type %s since it is not supported.", t)
            threading.Thread(target=self.pump(read_fn, lambda x: None), name="csdr_pump_thread").start()
            return
        self.receive_output(t, read_fn)

    def receive_output(self, t, read_fn):
        pass

    def pump(self, read, write):
        def copy():
            run = True
            while run:
                data = None
                try:
                    data = read()
                except ValueError:
                    pass
                if data is None or (isinstance(data, bytes) and len(data) == 0):
                    run = False
                else:
                    write(data)

        return copy

    def supports_type(self, t):
        return True
