BookmarkLocalStorage = function(){
};

BookmarkLocalStorage.prototype.getBookmarks = function(){
    return JSON.parse(window.localStorage.getItem("bookmarks")) || [];
};

BookmarkLocalStorage.prototype.setBookmarks = function(bookmarks){
    window.localStorage.setItem("bookmarks", JSON.stringify(bookmarks));
};

BookmarkLocalStorage.prototype.deleteBookmark = function(data) {
    if (data.id) data = data.id;
    var bookmarks = this.getBookmarks();
    bookmarks = bookmarks.filter(function(b) { return b.id !== data; });
    this.setBookmarks(bookmarks);
};
