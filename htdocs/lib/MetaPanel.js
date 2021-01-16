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
    this.el.find(".openwebrx-meta-autoclear").text("");
    this.el.find(".openwebrx-meta-slot").removeClass("active").removeClass("sync");
};

function DmrMetaSlot(el) {
    this.el = $(el);
}

DmrMetaSlot.prototype.update = function(data) {
    var id = "";
    var name = "";
    var target = "";
    var group = false;
    this.el[data['sync'] ? "addClass" : "removeClass"]("sync");
    if (data['sync'] && data['sync'] === "voice") {
        id = (data['additional'] && data['additional']['callsign']) || data['source'] || "";
        name = (data['additional'] && data['additional']['fname']) || "";
        if (data['type'] === "group") {
            target = "Talkgroup: ";
            group = true;
        }
        if (data['type'] === "direct") target = "Direct: ";
        target += data['target'] || "";
        this.el.addClass("active");
    } else {
        this.el.removeClass("active");
    }
    this.el.find(".openwebrx-dmr-id").text(id);
    this.el.find(".openwebrx-dmr-name").text(name);
    this.el.find(".openwebrx-dmr-target").text(target);
    this.el.find(".openwebrx-meta-user-image")[group ? "addClass" : "removeClass"]("group");
}

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
};

function YsfMetaPanel(el) {
    MetaPanel.call(this, el);
    this.modes = ['YSF'];
}

YsfMetaPanel.prototype = new MetaPanel();

YsfMetaPanel.prototype.update = function(data) {
    if (!this.isSupported(data)) return;

    var mode = " ";
    var source = "";
    var up = "";
    var down = "";
    if (data['mode'] && data['mode'] !== "") {
        mode = "Mode: " + data['mode'];
        source = data['source'] || "";
        if (data['lat'] && data['lon'] && data['source']) {
            source = "<a class=\"openwebrx-maps-pin\" href=\"map?callsign=" + data['source'] + "\" target=\"_blank\"></a>" + source;
        }
        up = data['up'] ? "Up: " + data['up'] : "";
        down = data['down'] ? "Down: " + data['down'] : "";
        this.el.find(".openwebrx-meta-slot").addClass("active");
    } else {
        this.el.find(".openwebrx-meta-slot").removeClass("active");
    }
    this.el.find(".openwebrx-ysf-mode").text(mode);
    this.el.find(".openwebrx-ysf-source").html(source);
    this.el.find(".openwebrx-ysf-up").text(up);
    this.el.find(".openwebrx-ysf-down").text(down);
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