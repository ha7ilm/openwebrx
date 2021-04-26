from owrx.admin.commands import Command
from owrx.config import Config
from owrx.bookmarks import Bookmarks


class MigrateCommand(Command):
    def run(self, args):
        print("Migrating configuration...")

        config = Config.get()
        # a key that is set will end up in the DynamicConfig, so this will transfer everything there
        for key, value in config.items():
            config[key] = value
        config.store()

        print("Migrating bookmarks...")
        # bookmarks just need to be saved
        b = Bookmarks.getSharedInstance()
        b.getBookmarks()
        b.store()

        print("Migration complete!")
