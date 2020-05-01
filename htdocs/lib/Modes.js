var Modes = {
    modes: [],
    features: {},
    panels: [],
    setModes:function(json){
        this.modes = json.map(function(m){ return new Mode(m); });
        this.updatePanels();
    },
    getModes:function(){
        return this.modes;
    },
    setFeatures:function(features){
        this.features = features;
        this.updatePanels();
    },
    findByModulation:function(modulation){
        matches = this.modes.filter(function(m) { return m.modulation === modulation; });
        if (matches.length) return matches[0]
    },
    registerModePanel: function(el) {
        this.panels.push(el);
    },
    updatePanels: function() {
        var init_complete = this.modes && this.features;
        this.panels.forEach(function(p) {
            p.render();
            if (init_complete) {
                p.startDemodulator();
            }
        });
    }
};

var Mode = function(json){
    this.modulation = json.modulation;
    this.name = json.name;
    this.type = json.type;
    this.requirements = json.requirements;
    if (json.bandpass) {
        this.bandpass = json.bandpass;
    }
    if (this.type === 'digimode') {
        this.underlying = json.underlying;
    }
};

Mode.prototype.isAvailable = function(){
    return this.requirements.map(function(r){
        return Modes.features[r];
    }).reduce(function(a, b){
        return a && b;
    }, true);
};
