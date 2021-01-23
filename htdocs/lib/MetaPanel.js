function MetaPanel(el) {
    this.el = el;
    this.modes = [];
}

MetaPanel.prototype.update = function(data) {
};

MetaPanel.prototype.isSupported = function(data) {
    return this.modes.includes(data.protocol);
};

MetaPanel.prototype.clear = function() {
    this.el.find(".openwebrx-meta-slot").removeClass("active").removeClass("sync");
};

function DmrMetaSlot(el) {
    this.el = $(el);
    this.clear();
}

DmrMetaSlot.prototype.update = function(data) {
    this.el[data['sync'] ? "addClass" : "removeClass"]("sync");
    if (data['sync'] && data['sync'] === "voice") {
        this.setId(data['additional'] && data['additional']['callsign'] || data['source']);
        this.setName(data['additional'] && data['additional']['fname']);
        this.setMode(['group', 'direct'].includes(data['type']) ? data['type'] : undefined);
        this.setTarget(data['target']);
        this.el.addClass("active");
    } else {
        this.clear();
    }
};

DmrMetaSlot.prototype.setId = function(id) {
    if (this.id === id) return;
    this.id = id;
    this.el.find('.openwebrx-dmr-id').text(id || '');
}

DmrMetaSlot.prototype.setName = function(name) {
    if (this.name === name) return;
    this.name = name;
    this.el.find('.openwebrx-dmr-name').text(name || '');
};

DmrMetaSlot.prototype.setMode = function(mode) {
    if (this.mode === mode) return;
    this.mode = mode;
    var classes = ['group', 'direct'].filter(function(c){
        return c !== mode;
    });
    this.el.removeClass(classes.join(' ')).addClass(mode);
}

DmrMetaSlot.prototype.setTarget = function(target) {
    if (this.target === target) return;
    this.target = target;
    this.el.find('.openwebrx-dmr-target').text(target || '');
}

DmrMetaSlot.prototype.clear = function() {
    this.setId();
    this.setName();
    this.setMode();
    this.setTarget();
    this.el.removeClass("active");
};

function DmrMetaPanel(el) {
    MetaPanel.call(this, el);
    this.modes = ['DMR'];
    this.slots = this.el.find('.openwebrx-meta-slot').toArray().map(function(el){
        return new DmrMetaSlot(el);
    });
}

DmrMetaPanel.prototype = new MetaPanel();

DmrMetaPanel.prototype.update = function(data) {
    if (!this.isSupported(data)) return;
    if (data['slot']) {
        var slot = this.slots[data['slot']];
        slot.update(data);
    } else {
        this.clear();
    }
}

DmrMetaPanel.prototype.clear = function() {
    MetaPanel.prototype.clear.call(this);
    this.el.find(".openwebrx-dmr-timeslot-panel").removeClass("muted");
    this.slots.forEach(function(slot) {
        slot.clear();
    });
};

function YsfMetaPanel(el) {
    MetaPanel.call(this, el);
    this.modes = ['YSF'];
    this.clear();
}

YsfMetaPanel.prototype = new MetaPanel();

YsfMetaPanel.prototype.update = function(data) {
    if (!this.isSupported(data)) return;
    this.setMode(data['mode']);

    if (data['mode'] && data['mode'] !== "") {
        this.setSource(data['source']);
        this.setLocation(data['lat'], data['lon'], data['source']);
        this.setUp(data['up']);
        this.setDown(data['down']);
        this.el.find(".openwebrx-meta-slot").addClass("active");
    } else {
        this.clear();
    }
};

YsfMetaPanel.prototype.clear = function() {
    MetaPanel.prototype.clear.call(this);
    this.setMode();
    this.setSource();
    this.setLocation();
    this.setUp();
    this.setDown();
};

YsfMetaPanel.prototype.setMode = function(mode) {
    if (this.mode === mode) return;
    this.mode = mode;
    this.el.find('.openwebrx-ysf-mode').text(mode || '');
};

YsfMetaPanel.prototype.setSource = function(source) {
    if (this.source === source) return;
    this.source = source;
    this.el.find('.openwebrx-ysf-source .callsign').text(source || '');
};

YsfMetaPanel.prototype.setLocation = function(lat, lon, callsign) {
    var hasLocation = lat && lon && callsign && callsign != '';
    if (hasLocation === this.hasLocation && this.callsign === callsign) return;
    this.hasLocation = hasLocation; this.callsign = callsign;
    var html = '';
    if (hasLocation) {
        html = '<a class="openwebrx-maps-pin" href="map?callsign=' + encodeURIComponent(callsign) + '" target="_blank"></a>';
    }
    this.el.find('.openwebrx-ysf-source .location').html(html);
};

YsfMetaPanel.prototype.setUp = function(up) {
    if (this.up === up) return;
    this.up = up;
    this.el.find('.openwebrx-ysf-up').text(up || '');
};

YsfMetaPanel.prototype.setDown = function(down) {
    if (this.down === down) return;
    this.down = down;
    this.el.find('.openwebrx-ysf-down').text(down || '');
}

MetaPanel.types = {
    dmr: DmrMetaPanel,
    ysf: YsfMetaPanel
};

$.fn.metaPanel = function() {
    return this.map(function() {
        var $self = $(this);
        if (!$self.data('metapanel')) {
            var matches = /^openwebrx-panel-metadata-([a-z]+)$/.exec($self.prop('id'));
            var constructor = matches && MetaPanel.types[matches[1]] || MetaPanel;
            $self.data('metapanel', new constructor($self));
        }
        return $self.data('metapanel');
    });
};