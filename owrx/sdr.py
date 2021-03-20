from owrx.config import Config
from owrx.property import PropertyManager, PropertyDeleted, PropertyDelegator, PropertyLayer, PropertyReadOnly
from owrx.feature import FeatureDetector, UnknownFeatureException
from owrx.source import SdrSource, SdrSourceEventClient
from functools import partial

import logging

logger = logging.getLogger(__name__)


class MappedSdrSources(PropertyDelegator):
    def __init__(self, pm: PropertyManager):
        self.subscriptions = {}
        super().__init__(PropertyLayer())
        for key, value in pm.items():
            self._addSource(key, value)
        pm.wire(self.handleSdrDeviceChange)

    def handleSdrDeviceChange(self, changes):
        for key, value in changes.items():
            if value is PropertyDeleted:
                if key in self:
                    del self[key]
            else:
                self._addSource(key, value)

    def handleDeviceUpdate(self, key, value, changes):
        if self.isDeviceValid(value) and key not in self:
            self._addSource(key, value)
        elif not self.isDeviceValid(value) and key in self:
            del self[key]

    def _addSource(self, key, value):
        if self.isDeviceValid(value):
            self[key] = self.buildNewSource(key, value)
        updateMethod = partial(self.handleDeviceUpdate, key, value)
        self.subscriptions[key] = [
            value.filter("type", "profiles").wire(updateMethod),
            value["profiles"].wire(updateMethod)
        ]

    def isDeviceValid(self, device):
        return self._hasProfiles(device) and self._sdrTypeAvailable(device)

    def _hasProfiles(self, device):
        return "profiles" in device and device["profiles"] and len(device["profiles"]) > 0

    def _sdrTypeAvailable(self, value):
        featureDetector = FeatureDetector()
        try:
            if not featureDetector.is_available(value["type"]):
                logger.error(
                    'The SDR source type "{0}" is not available. please check requirements.'.format(
                        value["type"]
                    )
                )
                return False
            return True
        except UnknownFeatureException:
            logger.error(
                'The SDR source type "{0}" is invalid. Please check your configuration'.format(value["type"])
            )
            return False

    def buildNewSource(self, id, props):
        sdrType = props["type"]
        className = "".join(x for x in sdrType.title() if x.isalnum()) + "Source"
        module = __import__("owrx.source.{0}".format(sdrType), fromlist=[className])
        cls = getattr(module, className)
        return cls(id, props)

    def _removeSource(self, key, source):
        source.shutdown()
        for sub in self.subscriptions[key]:
            sub.cancel()
        del self.subscriptions[key]

    def __setitem__(self, key, value):
        source = self[key] if key in self else None
        if source is value:
            return
        super().__setitem__(key, value)
        if source is not None:
            self._removeSource(key, source)

    def __delitem__(self, key):
        source = self[key] if key in self else None
        super().__delitem__(key)
        if source is not None:
            self._removeSource(key, source)


class SourceStateHandler(SdrSourceEventClient):
    def __init__(self, pm, key, source: SdrSource):
        self.pm = pm
        self.key = key
        self.source = source

    def selfDestruct(self):
        self.source.removeClient(self)

    def onFail(self):
        del self.pm[self.key]

    def onDisable(self):
        del self.pm[self.key]

    def onEnable(self):
        self.pm[self.key] = self.source

    def onShutdown(self):
        del self.pm[self.key]


class ActiveSdrSources(PropertyReadOnly):
    def __init__(self, pm: PropertyManager):
        self.handlers = {}
        self._layer = PropertyLayer()
        super().__init__(self._layer)
        for key, value in pm.items():
            self._addSource(key, value)
        pm.wire(self.handleSdrDeviceChange)

    def handleSdrDeviceChange(self, changes):
        for key, value in changes.items():
            if value is PropertyDeleted:
                self._removeSource(key)
            else:
                self._addSource(key, value)

    def isAvailable(self, source: SdrSource):
        return source.isEnabled() and not source.isFailed()

    def _addSource(self, key, source: SdrSource):
        if self.isAvailable(source):
            self._layer[key] = source
        self.handlers[key] = SourceStateHandler(self._layer, key, source)
        source.addClient(self.handlers[key])

    def _removeSource(self, key):
        self.handlers[key].selfDestruct()
        del self.handlers[key]
        if key in self._layer:
            del self._layer[key]


class SdrService(object):
    sources = None
    activeSources = None

    @staticmethod
    def getFirstSource():
        sources = SdrService.getActiveSources()
        if not sources:
            return None
        # TODO: configure default sdr in config? right now it will pick the first one off the list.
        return sources[list(sources.keys())[0]]

    @staticmethod
    def getSource(id):
        sources = SdrService.getActiveSources()
        if not sources:
            return None
        if id not in sources:
            return None
        return sources[id]

    @staticmethod
    def getAllSources():
        if SdrService.sources is None:
            SdrService.sources = MappedSdrSources(Config.get()["sdrs"])
        return SdrService.sources

    @staticmethod
    def getActiveSources():
        if SdrService.activeSources is None:
            SdrService.activeSources = ActiveSdrSources(SdrService.getAllSources())
        return SdrService.activeSources
