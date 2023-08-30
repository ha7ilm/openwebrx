function AprsMarker() {}

AprsMarker.prototype = new google.maps.OverlayView();

AprsMarker.prototype.isFacingEast = function(symbol) {
    var candidates = ''
    if (symbol.table === '/') {
        // primary table
        candidates = '(*<=>CFPUXYabefghjkpsuv[';
    } else {
        // alternate table
        candidates = 'hkluv';
    }
    return candidates.includes(symbol.symbol);
};

AprsMarker.prototype.draw = function() {
	var div = this.div;
	var overlay = this.overlay;
	if (!div || !overlay) return;

    if (this.symbol) {
        var tableId = this.symbol.table === '/' ? 0 : 1;
        div.style.background = 'url(aprs-symbols/aprs-symbols-24-' + tableId + '@2x.png)';
        div.style['background-size'] = '384px 144px';
        div.style['background-position-x'] = -(this.symbol.index % 16) * 24 + 'px';
        div.style['background-position-y'] = -Math.floor(this.symbol.index / 16) * 24 + 'px';
    }

    if (this.course) {
        if (this.symbol && !this.isFacingEast(this.symbol)) {
            // assume symbol points to the north
            div.style.transform = 'rotate(' + this.course + ' deg)';
        } else if (this.course > 180) {
            // symbol is pointing east
            // don't rotate more than 180 degrees, rather mirror
            div.style.transform = 'scalex(-1) rotate(' + (270 - this.course) + 'deg)'
        } else {
            // symbol is pointing east
            div.style.transform = 'rotate(' + (this.course - 90) + 'deg)';
        }
    } else {
        div.style.transform = null;
    }

    if (this.symbol.table !== '/' && this.symbol.table !== '\\') {
        overlay.style.display = 'block';
        overlay.style['background-position-x'] = -(this.symbol.tableindex % 16) * 24 + 'px';
        overlay.style['background-position-y'] = -Math.floor(this.symbol.tableindex / 16) * 24 + 'px';
    } else {
        overlay.style.display = 'none';
    }

    if (this.opacity) {
        div.style.opacity = this.opacity;
    } else {
        div.style.opacity = null;
    }

	var point = this.getProjection().fromLatLngToDivPixel(this.position);

	if (point) {
		div.style.left = point.x - 12 + 'px';
		div.style.top = point.y - 12 + 'px';
	}
};

AprsMarker.prototype.setOptions = function(options) {
    google.maps.OverlayView.prototype.setOptions.apply(this, arguments);
    this.draw();
};

AprsMarker.prototype.onAdd = function() {
    var div = this.div = document.createElement('div');

    div.style.position = 'absolute';
    div.style.cursor = 'pointer';
    div.style.width = '24px';
    div.style.height = '24px';

    var overlay = this.overlay = document.createElement('div');
    overlay.style.width = '24px';
    overlay.style.height = '24px';
    overlay.style.background = 'url(aprs-symbols/aprs-symbols-24-2@2x.png)';
    overlay.style['background-size'] = '384px 144px';
    overlay.style.display = 'none';

    div.appendChild(overlay);

	var self = this;
    div.addEventListener("click", function(event) {
        event.stopPropagation();
        google.maps.event.trigger(self, "click", event);
    });

    var panes = this.getPanes();
    panes.overlayImage.appendChild(div);
};

AprsMarker.prototype.onRemove = function() {
	if (this.div) {
		this.div.parentNode.removeChild(this.div);
		this.div = null;
	}
};

AprsMarker.prototype.getAnchorPoint = function() {
    return new google.maps.Point(0, -12);
};
