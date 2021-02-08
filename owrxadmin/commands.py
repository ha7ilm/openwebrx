from abc import ABC, ABCMeta, abstractmethod
from getpass import getpass
from owrx.users import UserList, User, DefaultPasswordClass
import sys
import random
import string


class Command(ABC):
    @abstractmethod
    def run(self, args):
        pass


class UserCommand(Command, metaclass=ABCMeta):
    def getUser(self, args):
        if args.user:
            return args.user
        else:
            if args.noninteractive:
                print("ERROR: User name not specified")
                sys.exit(1)
            else:
                return input("Please enter the user name: ")

    def getPassword(self, args, username):
        if args.noninteractive:
            print("Generating password for user {username}...".format(username=username))
            password = self.getRandomPassword()
            print('Password for {username} is "{password}".'.format(username=username, password=password))
            # TODO implement this threat
            print('This password is suitable for initial setup only, you will be asked to reset it on initial use.')
            print('This password cannot be recovered from the system, please copy it now.')
        else:
            password = getpass("Please enter the new password for {username}: ".format(username=username))
            confirm = getpass("Please confirm the new password: ")
            if password != confirm:
                print("ERROR: Password mismatch.")
                sys.exit(1)
        return password

    def getRandomPassword(self, length=10):
        printable = list(string.ascii_letters) + list(string.digits)
        return ''.join(random.choices(printable, k=length))


class NewUser(UserCommand):
    def run(self, args):
        username = self.getUser(args)
        userList = UserList()
        # early test to bypass the password stuff if the user already exists
        if username in userList:
            raise KeyError("User {username} already exists".format(username=username))

        password = self.getPassword(args, username)

        print("Creating user {username}...".format(username=username))
        user = User(name=username, enabled=True, password=DefaultPasswordClass(password))
        userList.addUser(user)


class DeleteUser(UserCommand):
    def run(self, args):
        username = self.getUser(args)
        print("Deleting user {username}...".format(username=username))
        userList = UserList()
        userList.deleteUser(username)


class ResetPassword(UserCommand):
    def run(self, args):
        username = self.getUser(args)
        password = self.getPassword(args, username)
        userList = UserList()
        userList[username].setPassword(DefaultPasswordClass(password))
        # this is a change to an object in the list, not the list itself
        # in this case, store() is explicit
        userList.store()


class DisableUser(UserCommand):
    def run(self, args):
        username = self.getUser(args)
        userList = UserList()
        userList[username].disable()
        userList.store()


class EnableUser(UserCommand):
    def run(self, args):
        username = self.getUser(args)
        userList = UserList()
        userList[username].enable()
        userList.store()


class ListUsers(Command):
    def run(self, args):
        userList = UserList()
        print("List of enabled users:")
        for u in userList.values():
            if args.all or u.enabled:
                print("  {name}".format(name=u.name))
