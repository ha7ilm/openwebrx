from owrx.version import openwebrx_version
from owrxadmin.commands import NewUser, DeleteUser
import argparse
import sys
import traceback


def main():
    print("OpenWebRX admin version {version}".format(version=openwebrx_version))

    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="One of the following commands: adduser, removeuser")
    parser.add_argument("--noninteractive", action="store_true", help="Don't ask for any user input (useful for automation)")
    parser.add_argument("--silent", action="store_true", help="Ignore errors (useful for automation)")
    parser.add_argument("-u", "--user")
    args = parser.parse_args()

    if args.command == "adduser":
        command = NewUser()
    elif args.command == "removeuser":
        command = DeleteUser()
    else:
        if not args.silent:
            print("Unknown command: {command}".format(command=args.command))
            sys.exit(1)
        sys.exit(0)

    try:
        command.run(args)
    except Exception:
        if not args.silent:
            print("Error running command:")
            traceback.print_exc()
            sys.exit(1)
        sys.exit(0)
