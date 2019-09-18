function AprsMarker() {}

AprsMarker.prototype = new google.maps.OverlayView();

AprsMarker.prototype.draw = function() {
	var div = this.div;
	var overlay = this.overlay;

    if (this.symbol) {
        var tableId = this.symbol.table == '/' ? 0 : 1;
        div.style.background = 'url(/aprs-symbols/aprs-symbols-24-' + tableId + '@2x.png)';
        div.style['background-size'] = '384px 144px';
        div.style['background-position-x'] = -(this.symbol.index % 16) * 24 + 'px';
        div.style['background-position-y'] = -Math.floor(this.symbol.index / 16) * 24 + 'px';
    }

    if (this.symbol.table != '/' && this.symbol.table != '\\') {
        overlay.style.display = 'block';
        overlay.style['background-position-x'] = -(this.symbol.tableindex % 16) * 24 + 'px';
        overlay.style['background-position-y'] = -Math.floor(this.symbol.tableindex / 16) * 24 + 'px';
    } else {
        overlay.style.display = 'none';
    }

	var point = this.getProjection().fromLatLngToDivPixel(this.position);

	if (point) {
		div.style.left = point.x - 12 + 'px';
		div.style.top = point.y - 12 + 'px';
	}
};

AprsMarker.prototype.onAdd = function() {
    var div = this.div = document.createElement('div');

    div.className = 'marker';

    div.style.position = 'absolute';
    div.style.cursor = 'pointer';
    div.style.width = '24px';
    div.style.height = '24px';

    var overlay = this.overlay = document.createElement('div');
    overlay.style.width = '24px';
    overlay.style.height = '24px';
    overlay.style.background = 'url(/aprs-symbols/aprs-symbols-24-2@2x.png)';
    overlay.style['background-size'] = '384px 144px';
    overlay.style.display = 'none';

    div.appendChild(overlay);

	var self = this;
    google.maps.event.addDomListener(div, "click", function(event) {
        event.stopPropagation();
        google.maps.event.trigger(self, "click", event);
    });

    var panes = this.getPanes();
    panes.overlayImage.appendChild(div);
}

AprsMarker.prototype.remove = function() {
	if (this.div) {
		this.div.parentNode.removeChild(this.div);
		this.div = null;
	}
};

AprsMarker.prototype.getAnchorPoint = function() {
    return new google.maps.Point(0, -12);
}
