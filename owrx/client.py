from owrx.config import Config
import threading

import logging

logger = logging.getLogger(__name__)


class TooManyClientsException(Exception):
    pass


class ClientRegistry(object):
    sharedInstance = None
    creationLock = threading.Lock()

    @staticmethod
    def getSharedInstance():
        with ClientRegistry.creationLock:
            if ClientRegistry.sharedInstance is None:
                ClientRegistry.sharedInstance = ClientRegistry()
        return ClientRegistry.sharedInstance

    def __init__(self):
        self.clients = []
        Config.get().wireProperty("max_clients", self._checkClientCount)
        super().__init__()

    def broadcast(self):
        n = self.clientCount()
        for c in self.clients:
            c.write_clients(n)

    def addClient(self, client):
        pm = Config.get()
        if len(self.clients) >= pm["max_clients"]:
            raise TooManyClientsException()
        self.clients.append(client)
        self.broadcast()

    def clientCount(self):
        return len(self.clients)

    def removeClient(self, client):
        try:
            self.clients.remove(client)
        except ValueError:
            pass
        self.broadcast()

    def _checkClientCount(self, new_count):
        logger.debug("new client count: %i", new_count)
        for client in self.clients[new_count:]:
            logger.debug("closing one connection...")
            client.close()
