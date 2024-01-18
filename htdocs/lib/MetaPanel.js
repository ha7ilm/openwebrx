function MetaPanel(el) {
    this.el = el;
    this.modes = [];
}

MetaPanel.prototype.update = function(data) {
};

MetaPanel.prototype.isSupported = function(data) {
    return this.modes.includes(data.protocol);
};

MetaPanel.prototype.isEnabled = function() {
    return true;
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
        this.setId(data['additional'] && data['additional']['callsign'] || data['talkeralias'] || data['source']);
        this.setName(data['additional'] && data['additional']['fname']);
        this.setMode(['group', 'direct'].includes(data['type']) ? data['type'] : undefined);
        this.setTarget(data['target']);
        this.setLocation(data['lat'], data['lon'], this.getCallsign(data));
        this.el.addClass("active");
    } else {
        this.clear();
    }
};

DmrMetaSlot.prototype.getCallsign = function(data) {
    if ('additional' in data) {
        return data['additional']['callsign'];
    }
    if ('talkeralias' in data) {
        var matches = /^([A-Z0-9]+)(\s.*)?$/.exec(data['talkeralias']);
        if (matches) return matches[1];
    }
};

DmrMetaSlot.prototype.setId = function(id) {
    if (this.id === id) return;
    this.id = id;
    this.el.find('.openwebrx-dmr-id .dmr-id').text(id || '');
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

DmrMetaSlot.prototype.setLocation = function(lat, lon, callsign) {
    var hasLocation = lat && lon && callsign && callsign != '';
    if (hasLocation === this.hasLocation && this.callsign === callsign) return;
    this.hasLocation = hasLocation; this.callsign = callsign;
    var html = '';
    if (hasLocation) {
        html = '<a class="openwebrx-maps-pin" href="map?callsign=' + encodeURIComponent(callsign) + '" target="_blank"><svg viewBox="0 0 20 35"><use xlink:href="static/gfx/svg-defs.svg#maps-pin"></use></svg></a>';
    }
    this.el.find('.openwebrx-dmr-id .location').html(html);
}

DmrMetaSlot.prototype.clear = function() {
    this.setId();
    this.setName();
    this.setMode();
    this.setTarget();
    this.setLocation();
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
        if (data['mode'].indexOf('data') < 0) {
            this.el.find(".openwebrx-meta-slot").addClass("active");
        }
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
        html = '<a class="openwebrx-maps-pin" href="map?callsign=' + encodeURIComponent(callsign) + '" target="_blank"><svg viewBox="0 0 20 35"><use xlink:href="static/gfx/svg-defs.svg#maps-pin"></use></svg></a>';
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

function DStarMetaPanel(el) {
    MetaPanel.call(this, el);
    this.modes = ['DSTAR'];
    this.clear();
}

DStarMetaPanel.prototype = new MetaPanel();

DStarMetaPanel.prototype.update = function(data) {
    if (!this.isSupported(data)) return;

    if (data['sync'] && data['sync'] == 'voice') {
        this.el.find(".openwebrx-meta-slot").addClass("active");
        this.setOurCall(data['ourcall']);
        this.setYourCall(data['yourcall']);
        this.setDeparture(data['departure']);
        this.setDestination(data['destination']);
        this.setMessage(data['message']);
        this.setLocation(data['lat'], data['lon'], data['ourcall']);
    } else {
        this.clear();
    }
};

DStarMetaPanel.prototype.setOurCall = function(ourcall) {
    if (this.ourcall === ourcall) return;
    this.ourcall = ourcall;
    this.el.find('.openwebrx-dstar-ourcall .callsign').text(ourcall || '');
};

DStarMetaPanel.prototype.setYourCall = function(yourcall) {
    if (this.yourcall === yourcall) return;
    this.yourcall = yourcall;
    this.el.find('.openwebrx-dstar-yourcall').text(yourcall || '');
};

DStarMetaPanel.prototype.setDeparture = function(departure) {
    if (this.departure === departure) return;
    this.departure = departure;
    this.el.find('.openwebrx-dstar-departure').text(departure || '');
};

DStarMetaPanel.prototype.setDestination = function(destination) {
    if (this.destination === destination) return;
    this.destination = destination;
    this.el.find('.openwebrx-dstar-destination').text(destination || '');
};

DStarMetaPanel.prototype.setMessage = function(message) {
    if (this.message === message) return;
    this.message = message;
    this.el.find('.openwebrx-dstar-message').text(message || '');
}

DStarMetaPanel.prototype.clear = function() {
    MetaPanel.prototype.clear.call(this);
    this.setOurCall();
    this.setYourCall();
    this.setDeparture();
    this.setDestination();
    this.setMessage();
    this.setLocation();
};

DStarMetaPanel.prototype.setLocation = function(lat, lon, callsign) {
    var hasLocation = lat && lon && callsign && callsign != '';
    if (hasLocation === this.hasLocation && this.callsign === callsign) return;
    this.hasLocation = hasLocation; this.callsign = callsign;
    var html = '';
    if (hasLocation) {
        html = '<a class="openwebrx-maps-pin" href="map?callsign=' + encodeURIComponent(callsign) + '" target="_blank"><svg viewBox="0 0 20 35"><use xlink:href="static/gfx/svg-defs.svg#maps-pin"></use></svg></a>';
    }
    this.el.find('.openwebrx-dstar-ourcall .location').html(html);
};

function NxdnMetaPanel(el) {
    MetaPanel.call(this, el);
    this.modes = ['NXDN'];
    this.clear();
}

NxdnMetaPanel.prototype = new MetaPanel();

NxdnMetaPanel.prototype.update = function(data) {
    if (!this.isSupported(data)) return;

    if (data['sync'] && data['sync'] === 'voice') {
        this.el.find(".openwebrx-meta-slot").addClass("active");
        this.setSource(data['additional'] && data['additional']['callsign'] || data['source']);
        this.setName(data['additional'] && data['additional']['fname']);
        this.setDestination(data['destination']);
        this.setMode(['conference', 'individual'].includes(data['type']) ? data['type'] : undefined);
    } else {
        this.clear();
    }
};

NxdnMetaPanel.prototype.setSource = function(source) {
    if (this.source === source) return;
    this.source = source;
    this.el.find('.openwebrx-nxdn-source').text(source || '');
};

NxdnMetaPanel.prototype.setName = function(name) {
    if (this.name === name) return;
    this.name = name;
    this.el.find('.openwebrx-nxdn-name').text(name || '');
};

NxdnMetaPanel.prototype.setDestination = function(destination) {
    if (this.destination === destination) return;
    this.destination = destination;
    this.el.find('.openwebrx-nxdn-destination').text(destination || '');
};

NxdnMetaPanel.prototype.setMode = function(mode) {
    if (this.mode === mode) return;
    this.mode = mode;

    var modes = ['individual', 'conference'];
    var classes = modes.filter(function(c){
        return c !== mode;
    });
    this.el.find('.openwebrx-meta-slot').removeClass(classes.join(' ')).addClass(mode);
};

NxdnMetaPanel.prototype.clear = function() {
    MetaPanel.prototype.clear.call(this);
    this.setMode();
    this.setSource();
    this.setName();
    this.setDestination();
};

function M17MetaPanel(el) {
    MetaPanel.call(this, el);
    this.modes = ['M17'];
    this.clear();
}

M17MetaPanel.prototype = new MetaPanel();

M17MetaPanel.prototype.update = function(data) {
    if (!this.isSupported(data)) return;

    if (data['sync'] && data['sync'] === 'voice') {
        this.el.find(".openwebrx-meta-slot").addClass("active");
        this.setSource(data['source']);
        this.setDestination(data['destination']);
    } else {
        this.clear();
    }
};

M17MetaPanel.prototype.setSource = function(source) {
    if (this.source === source) return;
    this.source = source;
    this.el.find('.openwebrx-m17-source').text(source || '');
};

M17MetaPanel.prototype.setDestination = function(destination) {
    if (this.destination === destination) return;
    this.destination = destination;
    this.el.find('.openwebrx-m17-destination').text(destination || '');
};

M17MetaPanel.prototype.clear = function() {
    MetaPanel.prototype.clear.call(this);
    this.setSource();
    this.setDestination();
};

function WfmMetaPanel(el) {
    MetaPanel.call(this, el);
    this.modes = ['WFM'];
    this.enabled = false;
    this.pi = '';
    this.timeout = false;
    // callsigns are only available in RBDS mode (US)
    this.callsign = false;
    this.clear();
}

WfmMetaPanel.prototype = new MetaPanel();

WfmMetaPanel.prototype.update = function(data) {
    var me = this;

    // automatically clear metadata panel when no RDS data is received for more than ten seconds
    if (this.timeout) clearTimeout(this.timeout);
    this.timeout = setTimeout(function(){
        me.clear();
    }, 10000);

    if (!this.isSupported(data)) return;
    if ('pi' in data && data.pi !== this.pi) {
        this.clear();
        this.pi = data.pi;
    }

    var $el = $(this.el);
    ['ps', 'prog_type', 'radiotext'].forEach(function(key) {
        if (key in data) {
            $el.find('.rds-' + key).text(data[key]);
        }
    });

    if ('callsign' in data) {
        this.callsign = true;
        $el.find('.rds-identifier').text(data.callsign);
    }

    if ('pi' in data && !this.callsign) {
        $el.find('.rds-identifier').text('PI: ' + data.pi);
    }

    if ('clock_time' in data) {
        var date = new Date(Date.parse(data.clock_time));
        $el.find('.rds-clock').text(date.toLocaleString([], {dateStyle: 'short', timeStyle: 'short'}));
    }
};

WfmMetaPanel.prototype.isSupported = function(data) {
    return this.modes.includes(data.mode);
};

WfmMetaPanel.prototype.setEnabled = function(enabled) {
    if (enabled === this.enabled) return;
    this.enabled = enabled;
    if (enabled) {
        $(this.el).html(
            '<div class="rds-container">' +
                '<div class="rds-identifier"></div>' +
                '<div class="rds-ps"></div>' +
                '<div class="rds-radiotext"></div>' +
                '<div class="rds-prog_type"></div>' +
                '<div class="rds-clock"></div>' +
            '</div>'
        );
    } else {
        $(this.el).emtpy()
    }
};

WfmMetaPanel.prototype.isEnabled = function() {
    return this.enabled;
};

WfmMetaPanel.prototype.clear = function() {
    $(this.el).find('.rds-identifier, .rds-ps, .rds-prog_type, .rds-radiotext, .rds-clock').text('');
    // display PI until we get the next callsign
    this.callsign = false;
};

MetaPanel.types = {
    dmr: DmrMetaPanel,
    ysf: YsfMetaPanel,
    dstar: DStarMetaPanel,
    nxdn: NxdnMetaPanel,
    m17: M17MetaPanel,
    wfm: WfmMetaPanel,
};

$.fn.metaPanel = function() {
    return this.map(function() {
        var $self = $(this);
        if (!$self.data('metapanel')) {
            var matches = /^openwebrx-panel-metadata-([a-z0-9]+)$/.exec($self.prop('id'));
            var constructor = matches && MetaPanel.types[matches[1]] || MetaPanel;
            $self.data('metapanel', new constructor($self));
        }
        return $self.data('metapanel');
    });
};