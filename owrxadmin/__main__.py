from owrx.version import openwebrx_version
from owrxadmin.commands import NewUserCommand
import argparse
import sys


def main():
    print("OpenWebRX admin version {version}".format(version=openwebrx_version))

    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="One of the following commands: adduser, removeuser")
    parser.add_argument("--noninteractive", action="store_true", help="Don't ask for any user input (useful for automation)")
    parser.add_argument("-u", "--user")
    args = parser.parse_args()

    if args.command == "adduser":
        NewUserCommand().run(args)
    elif args.command == "removeuser":
        print("removing user")
    else:
        print("Unknown command: {command}".format(command=args.command))
        sys.exit(1)
