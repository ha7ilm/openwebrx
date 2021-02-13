from owrx.controllers.template import WebpageController
from owrx.controllers.admin import AuthorizationMixin
from owrx.bookmarks import Bookmark, Bookmarks


class BookmarksController(AuthorizationMixin, WebpageController):
    def header_variables(self):
        variables = super().header_variables()
        variables["assets_prefix"] = "../"
        return variables

    def template_variables(self):
        variables = super().template_variables()
        variables["bookmarks"] = self.render_table()
        return variables

    def render_table(self):
        bookmarks = Bookmarks.getSharedInstance()
        return """
            <table class="table bookmarks">
                <tr>
                    <th>Name</th>
                    <th class="frequency">Frequency</th>
                    <th>Modulation</th>
                </tr>
                {bookmarks}
            </table>
        """.format(
            bookmarks="".join(self.render_bookmark(idx, b) for idx, b in enumerate(bookmarks.getBookmarks()))
        )

    def render_bookmark(self, idx: int, bookmark: Bookmark):
        return """
            <tr data-index="{index}">
                <td>{name}</td>
                <td class="frequency">{frequency}</td>
                <td>{modulation}</td>
            </tr>
        """.format(
            index=idx,
            name=bookmark.getName(),
            frequency=bookmark.getFrequency(),
            modulation=bookmark.getModulation(),
        )

    def indexAction(self):
        self.serve_template("settings/bookmarks.html", **self.template_variables())
