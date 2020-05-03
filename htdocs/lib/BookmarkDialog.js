$.fn.bookmarkDialog = function() {
    var $el = this;
    return {
        setModes: function(modes) {
            $el.find('#modulation').html(modes.map(function(m) {
                return '<option value="' + m.modulation + '">' + m.name + '</option>';
            }).join(''));
        }
    }
}