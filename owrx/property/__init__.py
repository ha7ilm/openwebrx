import logging

logger = logging.getLogger(__name__)


class Subscription(object):
    def __init__(self, subscriptee, subscriber):
        self.subscriptee = subscriptee
        self.subscriber = subscriber

    def call(self, *args, **kwargs):
        self.subscriber(*args, **kwargs)

    def cancel(self):
        self.subscriptee.unwire(self)


class Property(object):
    def __init__(self, value=None):
        self.value = value
        self.subscribers = []

    def getValue(self):
        return self.value

    def setValue(self, value):
        if self.value == value:
            return self
        self.value = value
        for c in self.subscribers:
            try:
                c.call(self.value)
            except Exception as e:
                logger.exception(e)
        return self

    def wire(self, callback):
        sub = Subscription(self, callback)
        self.subscribers.append(sub)
        if self.value is not None:
            sub.call(self.value)
        return sub

    def unwire(self, sub):
        try:
            self.subscribers.remove(sub)
        except ValueError:
            # happens when already removed before
            pass
        return self


class PropertyManager(object):
    def collect(self, *props):
        return PropertyManager(
            {name: self.getProperty(name) if self.hasProperty(name) else Property() for name in props}
        )

    def __init__(self, properties=None):
        self.properties = {}
        self.subscribers = []
        if properties is not None:
            for (name, prop) in properties.items():
                self.add(name, prop)

    def add(self, name, prop):
        self.properties[name] = prop

        def fireCallbacks(value):
            for c in self.subscribers:
                try:
                    c.call(name, value)
                except Exception as e:
                    logger.exception(e)

        prop.wire(fireCallbacks)
        return self

    def __contains__(self, name):
        return self.hasProperty(name)

    def __getitem__(self, name):
        return self.getPropertyValue(name)

    def __setitem__(self, name, value):
        if not self.hasProperty(name):
            self.add(name, Property())
        self.getProperty(name).setValue(value)

    def __dict__(self):
        return {k: v.getValue() for k, v in self.properties.items()}

    def hasProperty(self, name):
        return name in self.properties

    def getProperty(self, name):
        if not self.hasProperty(name):
            self.add(name, Property())
        return self.properties[name]

    def getPropertyValue(self, name):
        return self.getProperty(name).getValue()

    def wire(self, callback):
        sub = Subscription(self, callback)
        self.subscribers.append(sub)
        return sub

    def unwire(self, sub):
        try:
            self.subscribers.remove(sub)
        except ValueError:
            # happens when already removed before
            pass
        return self

    def defaults(self, other_pm):
        for (key, p) in self.properties.items():
            if p.getValue() is None:
                p.setValue(other_pm[key])
        return self
