function Header(el) {
    this.el = el;

    this.el.find('#openwebrx-main-buttons').find('[data-toggle-panel]').click(function () {
        toggle_panel($(this).data('toggle-panel'));
    });
};

Header.prototype.setDetails = function(details) {
    this.el.find('#webrx-rx-title').html(details['receiver_name']);
    var query = encodeURIComponent(details['receiver_gps']['lat'] + ',' + details['receiver_gps']['lon']);
    this.el.find('#webrx-rx-desc').html(details['receiver_location'] + ' | Loc: ' + details['locator'] + ', ASL: ' + details['receiver_asl'] + ' m, <a href="https://www.google.com/maps/search/?api=1&query=' + query + '" target="_blank" onclick="dont_toggle_rx_photo();">[maps]</a>');
    this.el.find('#webrx-rx-photo-title').html(details['photo_title']);
    this.el.find('#webrx-rx-photo-desc').html(details['photo_desc']);
};

$.fn.header = function() {
    if (!this.data('header')) {
        this.data('header', new Header(this));
    }
    return this.data('header');
};