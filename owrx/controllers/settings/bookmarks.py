from owrx.controllers.template import WebpageController
from owrx.controllers.admin import AuthorizationMixin
from owrx.bookmarks import Bookmark, Bookmarks
from owrx.modes import Modes
import json

import logging

logger = logging.getLogger(__name__)


class BookmarksController(AuthorizationMixin, WebpageController):
    def template_variables(self):
        variables = super().template_variables()
        variables["bookmarks"] = self.render_table()
        return variables

    def render_table(self):
        bookmarks = Bookmarks.getSharedInstance()

        def render_mode(m):
            return """
                <option value={mode}>{name}</option>
            """.format(
                mode=m.modulation,
                name=m.name,
            )

        return """
            <table class="table">
                <tr>
                    <th>Name</th>
                    <th class="frequency">Frequency</th>
                    <th>Modulation</th>
                    <th>Actions</th>
                </tr>
                {bookmarks}
                <tr class="inputs" style="display:none;">
                    <td><input class="form-control form-control-sm" type="text" name="name"></td>
                    <td><input class="form-control form-control-sm" type="number" step="1" name="frequency"></td>
                    <td><select class="form-control form-control-sm" name="modulation">{options}</select></td>
                    <td></td>
                </tr>
            </table>
        """.format(
            bookmarks="".join(self.render_bookmark(b) for b in bookmarks.getBookmarks()),
            options="".join(render_mode(m) for m in Modes.getAvailableModes()),
        )

    def render_bookmark(self, bookmark: Bookmark):
        mode = Modes.findByModulation(bookmark.getModulation())
        return """
            <tr data-id="{id}">
                <td>{name}</td>
                <td class="frequency">{frequency}</td>
                <td data-value="{modulation}">{modulation_name}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger bookmark-delete">delete</button>
                </td>
            </tr>
        """.format(
            id=id(bookmark),
            name=bookmark.getName(),
            frequency=bookmark.getFrequency(),
            modulation=bookmark.getModulation() if mode is None else mode.modulation,
            modulation_name=bookmark.getModulation() if mode is None else mode.name,
        )

    def _findBookmark(self, bookmark_id):
        bookmarks = Bookmarks.getSharedInstance()
        try:
            return next(b for b in bookmarks.getBookmarks() if id(b) == bookmark_id)
        except StopIteration:
            return None

    def update(self):
        bookmark_id = int(self.request.matches.group(1))
        bookmark = self._findBookmark(bookmark_id)
        if bookmark is None:
            self.send_response("{}", content_type="application/json", code=404)
            return
        try:
            data = json.loads(self.get_body())
            for key in ["name", "frequency", "modulation"]:
                if key in data:
                    value = data[key]
                    if key == "frequency":
                        value = int(value)
                    setattr(bookmark, key, value)
            Bookmarks.getSharedInstance().store()
            self.send_response("{}", content_type="application/json", code=200)
        except json.JSONDecodeError:
            self.send_response("{}", content_type="application/json", code=400)

    def new(self):
        bookmarks = Bookmarks.getSharedInstance()
        try:
            data = json.loads(self.get_body())
            # sanitize
            data = {k: data[k] for k in ["name", "frequency", "modulation"]}
            bookmark = Bookmark(data)

            bookmarks.addBookmark(bookmark)
            bookmarks.store()
            self.send_response(json.dumps({"bookmark_id": id(bookmark)}), content_type="application/json", code=200)
        except json.JSONDecodeError:
            self.send_response("{}", content_type="application/json", code=400)

    def delete(self):
        bookmark_id = int(self.request.matches.group(1))
        bookmark = self._findBookmark(bookmark_id)
        if bookmark is None:
            self.send_response("{}", content_type="application/json", code=404)
            return
        bookmarks = Bookmarks.getSharedInstance()
        bookmarks.removeBookmark(bookmark)
        bookmarks.store()
        self.send_response("{}", content_type="application/json", code=200)

    def indexAction(self):
        self.serve_template("settings/bookmarks.html", **self.template_variables())
