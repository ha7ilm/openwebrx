function BookmarkBar() {
    var me = this;
    me.localBookmarks = new BookmarkLocalStorage();
    me.$container = $("#openwebrx-bookmarks-container");
    me.bookmarks = {};

    me.$container.on('click', '.bookmark', function(e){
        var $bookmark = $(e.target).closest('.bookmark');
        me.$container.find('.bookmark').removeClass('selected');
        var b = $bookmark.data();
        if (!b || !b.frequency || !b.modulation) return;
        demodulator_set_offset_frequency(0, b.frequency - center_freq);
        demodulator_analog_replace(b.modulation);
        $bookmark.addClass('selected');
    });

    me.$container.on('click', '.action[data-action=edit]', function(e){
        e.stopPropagation();
        var $bookmark = $(e.target).closest('.bookmark');
        me.showEditDialog($bookmark.data());
    });

    me.$container.on('click', '.action[data-action=delete]', function(e){
        e.stopPropagation();
        var $bookmark = $(e.target).closest('.bookmark');
        me.localBookmarks.deleteBookmark($bookmark.data());
        me.loadLocalBookmarks();
    });

    var $bookmarkButton = $('#openwebrx-panel-receiver .openwebrx-bookmark-button');
    if (typeof(Storage) !== 'undefined') {
        $bookmarkButton.show();
    } else {
        $bookmarkButton.hide();
    }
    $bookmarkButton.click(function(){
        me.showEditDialog();
    });

    me.$dialog = $("#openwebrx-dialog-bookmark");
    me.$dialog.find('.openwebrx-button[data-action=cancel]').click(function(){
        me.$dialog.hide();
    });
    me.$dialog.find('.openwebrx-button[data-action=submit]').click(function(){
        me.storeBookmark();
    });
    me.$dialog.find('form').on('submit', function(e){
        e.preventDefault();
        me.storeBookmark();
    });
}

BookmarkBar.prototype.position = function(){
    var range = get_visible_freq_range();
    $('#openwebrx-bookmarks-container .bookmark').each(function(){
        $(this).css('left', scale_px_from_freq($(this).data('frequency'), range));
    });
}

BookmarkBar.prototype.loadLocalBookmarks = function(){
    var bwh = bandwidth / 2;
    var start = center_freq - bwh;
    var end = center_freq + bwh;
    var bookmarks = this.localBookmarks.getBookmarks().filter(function(b){
        return b.frequency >= start && b.frequency <= end;
    });
    this.replace_bookmarks(bookmarks, 'local', true);
}

BookmarkBar.prototype.replace_bookmarks = function(bookmarks, source, editable) {
    editable = !!editable;
    bookmarks = bookmarks.map(function(b){
        b.source = source;
        b.editable = editable;
        return b;
    });
    this.bookmarks[source] = bookmarks;
    this.render();
}

BookmarkBar.prototype.render = function(){
    var bookmarks = Object.values(this.bookmarks).reduce(function(l, v){ return l.concat(v); });
    bookmarks = bookmarks.sort(function(a, b){ return a.frequency - b.frequency; });
    var elements = bookmarks.map(function(b){
        $bookmark = $(
            '<div class="bookmark" data-source="' + b.source + '"' + (b.editable?' editable="editable"':'') + '>' +
                '<div class="bookmark-actions">' +
                    '<div class="openwebrx-button action" data-action="edit"><img src="static/gfx/openwebrx-edit.png"></div>' +
                    '<div class="openwebrx-button action" data-action="delete"><img src="static/gfx/openwebrx-trashcan.png"></div>' +
                '</div>' +
                '<div class="bookmark-content">' + b.name + '</div>' +
            '</div>'
        );
        $bookmark.data(b);
        return $bookmark;
    });
    this.$container.find('.bookmark').remove();
    this.$container.append(elements);
	this.position();
}

BookmarkBar.prototype.showEditDialog = function(bookmark) {
    var $form = this.$dialog.find("form");
    if (!bookmark) {
        bookmark = {
            name: "",
            frequency: center_freq + demodulators[0].offset_frequency,
            modulation: demodulators[0].subtype
        }
    }
    ['name', 'frequency', 'modulation'].forEach(function(key){
        $form.find('#' + key).val(bookmark[key]);
    });
    this.$dialog.data('id', bookmark.id);
    this.$dialog.show();
    this.$dialog.find('#name').focus();
}

BookmarkBar.prototype.storeBookmark = function() {
    var me = this;
    var bookmark = {};
    var valid = true;
    ['name', 'frequency', 'modulation'].forEach(function(key){
        var $input = me.$dialog.find('#' + key);
        valid = valid && $input[0].checkValidity();
        bookmark[key] = $input.val();
    });
    if (!valid) {
        me.$dialog.find("form :submit").click();
        return;
    }
    bookmark.frequency = Number(bookmark.frequency);

    var bookmarks = me.localBookmarks.getBookmarks();

    bookmark.id = me.$dialog.data('id');
    if (!bookmark.id) {
        if (bookmarks.length) {
            bookmark.id = 1 + Math.max.apply(Math, bookmarks.map(function(b){ return b.id || 0; }));
        } else {
            bookmark.id = 1;
        }
    }

    bookmarks = bookmarks.filter(function(b) { return b.id != bookmark.id; });
    bookmarks.push(bookmark);

    me.localBookmarks.setBookmarks(bookmarks);
    me.loadLocalBookmarks();
    me.$dialog.hide();
}

BookmarkLocalStorage = function(){
}

BookmarkLocalStorage.prototype.getBookmarks = function(){
    return JSON.parse(window.localStorage.getItem("bookmarks")) || [];
}

BookmarkLocalStorage.prototype.setBookmarks = function(bookmarks){
    window.localStorage.setItem("bookmarks", JSON.stringify(bookmarks));
}

BookmarkLocalStorage.prototype.deleteBookmark = function(data) {
    if (data.id) data = data.id;
    var bookmarks = this.getBookmarks();
    bookmarks = bookmarks.filter(function(b) { return b.id != data; });
    this.setBookmarks(bookmarks);
}




