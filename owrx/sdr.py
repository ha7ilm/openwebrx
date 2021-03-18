from owrx.config import Config
from owrx.property import PropertyManager, PropertyDeleted, PropertyDelegator, PropertyLayer
from owrx.feature import FeatureDetector, UnknownFeatureException
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
                del self[key]
            else:
                self._addSource(key, value)

    def handleDeviceUpdate(self, key, value, changes):
        if self.isDeviceValid(value) and key not in self:
            self._addSource(key, value)
        elif not self.isDeviceValid(value) and key in self:
            self._removeSource(key)

    def _addSource(self, key, value):
        if self.isDeviceValid(value):
            self[key] = self.buildNewSource(key, value)
        updateMethod = partial(self.handleDeviceUpdate, key, value)
        self.subscriptions[key] = [
            value.filter("type", "profiles").wire(updateMethod),
            value["profiles"].wire(updateMethod)
        ]

    def _removeSource(self, key):
        if key in self:
            self[key].shutdown()
        for sub in self.subscriptions[key]:
            sub.cancel()
        del self.subscriptions[key]

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

    def __setitem__(self, key, value):
        if key in self:
            self._removeSource(key)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        if key in self:
            self._removeSource(key)
        super().__delitem__(key)


class SdrService(object):
    sources = None

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
        return {
            key: s
            for key, s in SdrService.getAllSources().items()
            if not s.isFailed() and s.isEnabled()
        }
