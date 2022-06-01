from owrx.admin.commands import NewUser, DeleteUser, ResetPassword, ListUsers, DisableUser, EnableUser, HasUser
import sys
import traceback


def add_admin_parser(moduleparser):
    subparsers = moduleparser.add_subparsers(title="Commands", dest="command")

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

    hasuser_parser = subparsers.add_parser("hasuser", help="Test if a user exists")
    hasuser_parser.add_argument("user", help="Username to be checked")
    hasuser_parser.set_defaults(cls=HasUser)

    moduleparser.add_argument(
        "--noninteractive", action="store_true", help="Don't ask for any user input (useful for automation)"
    )
    moduleparser.add_argument("--silent", action="store_true", help="Ignore errors (useful for automation)")


def run_admin_action(parser, args):
    if hasattr(args, "cls"):
        command = args.cls()
    else:
        if not hasattr(args, "silent") or not args.silent:
            parser.print_help()
            return 1
        return 0

    try:
        return command.run(args)
    except Exception:
        if not hasattr(args, "silent") or not args.silent:
            print("Error running command:")
            traceback.print_exc()
            return 1
        return 0
