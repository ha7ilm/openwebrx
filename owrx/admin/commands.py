from abc import ABC, ABCMeta, abstractmethod
from getpass import getpass
from owrx.users import UserList, User, DefaultPasswordClass
import sys
import random
import string
import os


class Command(ABC):
    @abstractmethod
    def run(self, args):
        pass


class UserCommand(Command, metaclass=ABCMeta):
    def getPassword(self, args, username):
        if args.noninteractive:
            if "OWRX_PASSWORD" in os.environ:
                password = os.environ["OWRX_PASSWORD"]
                generated = False
            else:
                print("Generating password for user {username}...".format(username=username))
                password = self.getRandomPassword()
                generated = True
                print('Password for {username} is "{password}".'.format(username=username, password=password))
                print('This password is suitable for initial setup only, you will be asked to reset it on initial use.')
                print('This password cannot be recovered from the system, please copy it now.')
        else:
            password = getpass("Please enter the new password for {username}: ".format(username=username))
            confirm = getpass("Please confirm the new password: ")
            if password != confirm:
                raise ValueError("Password mismatch")
            generated = False
        return password, generated

    def getRandomPassword(self, length=10):
        printable = list(string.ascii_letters) + list(string.digits)
        return ''.join(random.choices(printable, k=length))


class NewUser(UserCommand):
    def run(self, args):
        username = args.user
        userList = UserList()
        # early test to bypass the password stuff if the user already exists
        if username in userList:
            raise KeyError("User {username} already exists".format(username=username))

        password, generated = self.getPassword(args, username)

        print("Creating user {username}...".format(username=username))
        user = User(name=username, enabled=True, password=DefaultPasswordClass(password), must_change_password=generated)
        userList.addUser(user)


class DeleteUser(UserCommand):
    def run(self, args):
        username = args.user
        print("Deleting user {username}...".format(username=username))
        userList = UserList()
        userList.deleteUser(username)


class ResetPassword(UserCommand):
    def run(self, args):
        username = args.user
        password, generated = self.getPassword(args, username)
        userList = UserList()
        userList[username].setPassword(DefaultPasswordClass(password), must_change_password=generated)
        # this is a change to an object in the list, not the list itself
        # in this case, store() is explicit
        userList.store()


class DisableUser(UserCommand):
    def run(self, args):
        username = args.user
        userList = UserList()
        userList[username].disable()
        userList.store()


class EnableUser(UserCommand):
    def run(self, args):
        username = args.user
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


class HasUser(Command):
    """
    internal command used by the debian config scripts to test if the admin user has already been created
    """
    def run(self, args):
        userList = UserList()
        if args.user in userList:
            if not args.silent:
                print('User "{name}" exists.'.format(name=args.user))
            return 0
        else:
            if not args.silent:
                print('User "{name}" does not exist.'.format(name=args.user))
            # in bash, a return code > 0 is interpreted as "false"
            return 1
