from owrx.config import Config
from abc import ABC, ABCMeta, abstractmethod
from typing import List

import logging

logger = logging.getLogger(__name__)


class AudioChopperProfile(ABC):
    @abstractmethod
    def getInterval(self):
        pass

    @abstractmethod
    def getFileTimestampFormat(self):
        pass

    @abstractmethod
    def decoder_commandline(self, file):
        pass


class ProfileSourceSubscriber(ABC):
    @abstractmethod
    def onProfilesChanged(self):
        pass


class ProfileSource(ABC):
    def __init__(self):
        self.subscribers = []

    @abstractmethod
    def getProfiles(self) -> List[AudioChopperProfile]:
        pass

    def subscribe(self, subscriber: ProfileSourceSubscriber):
        if subscriber in self.subscribers:
            return
        self.subscribers.append(subscriber)

    def unsubscribe(self, subscriber: ProfileSourceSubscriber):
        if subscriber not in self.subscribers:
            return
        self.subscribers.remove(subscriber)

    def fireProfilesChanged(self):
        for sub in self.subscribers.copy():
            try:
                sub.onProfilesChanged()
            except Exception:
                logger.exception("Error while notifying profile subscriptions")


class ConfigWiredProfileSource(ProfileSource, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self.configSub = None

    @abstractmethod
    def getPropertiesToWire(self) -> List[str]:
        pass

    def subscribe(self, subscriber: ProfileSourceSubscriber):
        super().subscribe(subscriber)
        if self.subscribers and self.configSub is None:
            self.configSub = Config.get().filter(*self.getPropertiesToWire()).wire(self.fireProfilesChanged)

    def unsubscribe(self, subscriber: ProfileSourceSubscriber):
        super().unsubscribe(subscriber)
        if not self.subscribers and self.configSub is not None:
            self.configSub.cancel()
            self.configSub = None

    def fireProfilesChanged(self, *args):
        super().fireProfilesChanged()


class StaticProfileSource(ProfileSource):
    def __init__(self, profiles: List[AudioChopperProfile]):
        super().__init__()
        self.profiles = profiles

    def getProfiles(self) -> List[AudioChopperProfile]:
        return self.profiles
