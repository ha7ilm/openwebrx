from owrx.version import openwebrx_version
from owrxadmin.commands import NewUser, DeleteUser, ResetPassword, ListUsers, DisableUser, EnableUser
import argparse
import sys
import traceback
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    adduser_parser = subparsers.add_parser("adduser", help="Add a new user")
    adduser_parser.add_argument("user", help="Username to be added")
    adduser_parser.set_defaults(cls=NewUser)

    removeuser_parser = subparsers.add_parser("removeuser", help="Remove an existing user")
    removeuser_parser.add_argument("user", help="Username to be remvoed")
    removeuser_parser.set_defaults(cls=DeleteUser)

    resetpassword_parser = subparsers.add_parser("resetpassword", help="Reset a user's password")
    resetpassword_parser.add_argument("user", help="Username to be remvoed")
    resetpassword_parser.set_defaults(cls=ResetPassword)

    listusers_parser = subparsers.add_parser("listusers", help="List enabled users")
    listusers_parser.add_argument("-a", "--all", action="store_true", help="Show all users (including disabled ones)")
    listusers_parser.set_defaults(cls=ListUsers)

    disableuser_parser = subparsers.add_parser("disableuser", help="Disable a user")
    disableuser_parser.add_argument("user", help="Username to be disabled")
    disableuser_parser.set_defaults(cls=DisableUser)

    enableuser_parser = subparsers.add_parser("enableuser", help="Enable a user")
    enableuser_parser.add_argument("user", help="Username to be enabled")
    enableuser_parser.set_defaults(cls=EnableUser)

    parser.add_argument("-v", "--version", action="store_true", help="Show the software version")
    parser.add_argument(
        "--noninteractive", action="store_true", help="Don't ask for any user input (useful for automation)"
    )
    parser.add_argument("--silent", action="store_true", help="Ignore errors (useful for automation)")
    args = parser.parse_args()

    if args.version:
        print("OpenWebRX Admin CLI version {version}".format(version=openwebrx_version))
        sys.exit(0)

    if hasattr(args, "cls"):
        command = args.cls()
    else:
        if not args.silent:
            parser.print_help()
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
