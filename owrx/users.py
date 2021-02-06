from abc import ABC, abstractmethod
from owrx.config import CoreConfig
import json
import hashlib
import os

import logging

logger = logging.getLogger(__name__)


class PasswordException(Exception):
    pass


class Password(ABC):
    @staticmethod
    def from_dict(d: dict):
        if "encoding" not in d:
            raise PasswordException("password encoding not set")
        if d["encoding"] == "string":
            return CleartextPassword(d)
        elif d["encoding"] == "hash":
            return HashedPassword(d)
        raise PasswordException("invalid passord encoding: {0}".format(d["type"]))

    @abstractmethod
    def is_valid(self, inp: str) -> bool:
        pass

    @abstractmethod
    def toJson(self) -> dict:
        pass


class CleartextPassword(Password):
    def __init__(self, pwinfo):
        if isinstance(pwinfo, str):
            self._value = pwinfo
        elif isinstance(pwinfo, dict):
            self._value = pwinfo["value"]
        else:
            raise ValueError("invalid argument to ClearTextPassword()")

    def is_valid(self, inp: str) -> bool:
        return self._value == inp

    def toJson(self) -> dict:
        return {
            "encoding": "string",
            "value": self._value
        }


class HashedPassword(Password):
    def __init__(self, pwinfo, algorithm="sha256"):
        self.iterations = 100000
        if (isinstance(pwinfo, str)):
            self._createFromString(pwinfo, algorithm)
        else:
            self._loadFromDict(pwinfo)

    def _createFromString(self, pw: str, algorithm: str):
        self._algorithm = algorithm
        self._salt = os.urandom(32)
        dk = hashlib.pbkdf2_hmac(self._algorithm, pw.encode(), self._salt, self.iterations)
        self._hash = dk.hex()
        pass

    def _loadFromDict(self, d: dict):
        self._hash = d["value"]
        self._algorithm = d["algorithm"]
        self._salt = bytes.fromhex(d["salt"])
        pass

    def is_valid(self, inp: str) -> bool:
        dk = hashlib.pbkdf2_hmac(self._algorithm, inp.encode(), self._salt, self.iterations)
        return dk.hex() == self._hash

    def toJson(self) -> dict:
        return {
            "encoding": "hash",
            "value": self._hash,
            "algorithm": self._algorithm,
            "salt": self._salt.hex(),
        }


DefaultPasswordClass = HashedPassword


class User(object):
    def __init__(self, name: str, enabled: bool, password: Password):
        self.name = name
        self.enabled = enabled
        self.password = password

    def toJson(self):
        return {
            "user": self.name,
            "enabled": self.enabled,
            "password": self.password.toJson()
        }


class UserList(object):
    sharedInstance = None

    @staticmethod
    def getSharedInstance():
        if UserList.sharedInstance is None:
            UserList.sharedInstance = UserList()
        return UserList.sharedInstance

    def __init__(self):
        self.users = self._loadUsers()

    def _getUsersFile(self):
        config = CoreConfig()
        return "{data_directory}/users.json".format(data_directory=config.get_data_directory())

    def _loadUsers(self):
        usersFile = self._getUsersFile()
        try:
            with open(usersFile, "r") as f:
                users_json = json.load(f)

            return {u.name: u for u in [self._jsonToUser(d) for d in users_json]}
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            logger.exception("error while parsing users file %s", usersFile)
            return {}
        except Exception:
            logger.exception("error while processing users from %s", usersFile)
            return {}

    def _jsonToUser(self, d):
        if "user" in d and "password" in d and "enabled" in d:
            return User(d["user"], d["enabled"], Password.from_dict(d["password"]))

    def _userToJson(self, u):
        return u.toJson()

    def _store(self):
        usersFile = self._getUsersFile()
        users = [u.toJson() for u in self.users.values()]
        try:
            with open(usersFile, "w") as f:
                json.dump(users, f, indent=4)
        except Exception:
            logger.exception("error while writing users file %s", usersFile)

    def _getUsername(self, user):
        if isinstance(user, User):
            return user.name
        elif isinstance(user, str):
            return user
        else:
            raise ValueError("invalid user type")

    def addUser(self, user: User):
        self[user.name] = user

    def deleteUser(self, user):
        del self[self._getUsername(user)]

    def __delitem__(self, key):
        if key not in self.users:
            raise KeyError("User {user} doesn't exist".format(user=key))
        del self.users[key]
        self._store()

    def __getitem__(self, item):
        return self.users[item]

    def __contains__(self, item):
        return item in self.users

    def __setitem__(self, key, value):
        if key in self.users:
            raise KeyError("User {user} already exists".format(user=key))
        self.users[key] = value
        self._store()
