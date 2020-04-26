var Modes = {
    modes: [],
    features: {},
    setModes:function(json){
        this.modes = json.map(function(m){ return new Mode(m); });
    },
    setFeatures:function(features){
        this.features = features;
    },
    findByModulation:function(modulation){
        matches = this.modes.filter(function(m) { return m.modulation === modulation; });
        if (matches.length) return matches[0]
    }
}

var Mode = function(json){
    this.modulation = json.modulation;
    this.name = json.name;
    this.requirements = json.requirements;
};

Mode.prototype.isAvailable = function(){
    return this.requirements.map(function(r){
        return Modes.features[r];
    }).reduce(function(a, b){
        return a && b;
    }, true);
}