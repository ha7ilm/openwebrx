from owrx.admin.commands import Command
from owrx.config import Config
from owrx.bookmarks import Bookmarks


class MigrateCommand(Command):
    # these keys have been moved to openwebrx.conf
    blacklisted_keys = [
        "temporary_directory",
        "web_port",
        "aprs_symbols_path",
    ]

    def run(self, args):
        print("Migrating configuration...")

        config = Config.get()
        # a key that is set will end up in the DynamicConfig, so this will transfer everything there
        for key, value in config.items():
            if key not in MigrateCommand.blacklisted_keys:
                config[key] = value
        config.store()

        print("Migrating bookmarks...")
        # bookmarks just need to be saved
        b = Bookmarks.getSharedInstance()
        b.getBookmarks()
        b.store()

        print("Migration complete!")
