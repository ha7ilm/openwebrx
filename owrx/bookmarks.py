import json


class Bookmark(object):
    def __init__(self, j):
        self.name = j["name"]
        self.frequency = j["frequency"]
        self.modulation = j["modulation"]

    def getName(self):
        return self.name

    def getFrequency(self):
        return self.frequency

    def getModulation(self):
        return self.modulation

    def __dict__(self):
        return {
            "name": self.getName(),
            "frequency": self.getFrequency(),
            "modulation": self.getModulation(),
        }


class Bookmarks(object):
    sharedInstance = None
    @staticmethod
    def getSharedInstance():
        if Bookmarks.sharedInstance is None:
            Bookmarks.sharedInstance = Bookmarks()
        return Bookmarks.sharedInstance

    def __init__(self):
        f = open("bookmarks.json", "r")
        bookmarks_json = json.load(f)
        f.close()
        self.bookmarks = [Bookmark(d) for d in bookmarks_json]

    def getBookmarks(self, range):
        (lo, hi) = range
        return [b for b in self.bookmarks if lo <= b.getFrequency() <= hi]
