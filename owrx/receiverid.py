import re
import logging
import hashlib
import hmac
from datetime import datetime, timezone
from owrx.config import Config

logger = logging.getLogger(__name__)


keyRegex = re.compile("^([a-zA-Z]+)-([0-9a-f]{32})-([0-9a-f]{64})$")
keyChallengeRegex = re.compile("^([a-zA-Z]+)-([0-9a-f]{32})-([0-9a-f]{32})$")
headerRegex = re.compile("^ReceiverId (.*)$")


class KeyException(Exception):
    pass


class Key(object):
    def __init__(self, keyString):
        matches = keyRegex.match(keyString)
        if not matches:
            raise KeyException("invalid key format")
        self.source = matches.group(1)
        self.id = matches.group(2)
        self.secret = matches.group(3)


class KeyChallenge(object):
    def __init__(self, challengeString):
        matches = keyChallengeRegex.match(challengeString)
        if not matches:
            raise KeyException("invalid key challenge format")
        self.source = matches.group(1)
        self.id = matches.group(2)
        self.challenge = matches.group(3)


class KeyResponse(object):
    def __init__(self, source, id, time, signature):
        self.source = source
        self.id = id
        self.time = time
        self.signature = signature

    def __str__(self):
        return "{source}-{id}-{time}-{signature}".format(
            source=self.source,
            id=self.id,
            time=self.time,
            signature=self.signature,
        )


class ReceiverId(object):
    @staticmethod
    def getResponseHeader(requestHeader):
        matches = headerRegex.match(requestHeader)
        if not matches:
            raise KeyException("invalid authorization header")
        challenges = [KeyChallenge(i) for i in matches.group(1).split(",")]

        def signChallenge(challenge):
            key = ReceiverId.findKey(challenge)
            if key is None:
                return
            return ReceiverId.signChallenge(challenge, key)

        responses = [signChallenge(c) for c in challenges]
        return ",".join(str(r) for r in responses if r is not None)

    @staticmethod
    def findKey(challenge):
        def parseKey(keyString):
            try:
                return Key(keyString)
            except KeyException as e:
                logger.error(e)

        config = Config.get()
        if "receiver_keys" not in config or config["receiver_keys"] is None:
            return None
        keys = [parseKey(keyString) for keyString in config["receiver_keys"]]
        keys = [key for key in keys if key is not None]
        matching_keys = [key for key in keys if key.source == challenge.source and key.id == challenge.id]
        if matching_keys:
            return matching_keys[0]
        return None

    @staticmethod
    def signChallenge(challenge, key):
        now = datetime.utcnow().replace(microsecond=0, tzinfo=timezone.utc)
        now_bytes = int(now.timestamp()).to_bytes(4, byteorder="big")
        m = hmac.new(bytes.fromhex(key.secret), digestmod=hashlib.sha256)
        m.update(bytes.fromhex(challenge.challenge))
        m.update(now_bytes)
        return KeyResponse(challenge.source, challenge.id, now_bytes.hex(), m.hexdigest())
