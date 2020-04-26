var Modes = {
    modes: [],
    features: {},
    setModes:function(json){
        this.modes = json.map(function(m){ return new Mode(m); });
        this.updateModePanel();
    },
    setFeatures:function(features){
        this.features = features;
        this.updateModePanel();
    },
    findByModulation:function(modulation){
        matches = this.modes.filter(function(m) { return m.modulation === modulation; });
        if (matches.length) return matches[0]
    },
    updateModePanel:function() {
        var available = this.modes.filter(function(m){ return m.isAvailable(); });
        var normalModes = available.filter(function(m){ return m.type === 'analog'; });
        var digiModes = available.filter(function(m){ return m.type === 'digimode'; });

        var html = []

        var buttons = normalModes.map(function(m){
            return $(
                '<div class="openwebrx-button openwebrx-demodulator-button"' +
                'id="openwebrx-button-' + m.modulation + '"' +
                'onclick="demodulator_analog_replace(\'' + m.modulation + '\');">' +
                m.name + '</div>'
            );
        });

        var index = 0;
        var arrayLength = buttons.length;
        var chunks = [];

        for (index = 0; index < arrayLength; index += 5) {
            chunks.push(buttons.slice(index, index + 5));
        }

        html.push.apply(html, chunks.map(function(chunk){
            $line = $('<div class="openwebrx-panel-line openwebrx-panel-flex-line"></div>');
            $line.append.apply($line, chunk);
            return $line
        }));

        html.push($(
            '<div class="openwebrx-panel-line openwebrx-panel-flex-line">' +
                '<div class="openwebrx-button openwebrx-demodulator-button" id="openwebrx-button-dig" onclick="demodulator_digital_replace_last();">DIG</div>' +
                '<select id="openwebrx-secondary-demod-listbox" onchange="secondary_demod_listbox_changed();">' +
                    '<option value="none"></option>' +
                    digiModes.map(function(m){
                        return '<option value="' + m.modulation + '">' + m.name + '</option>';
                    }).join('') +
                '</select>' +
            '</div>'
        ));

        $("#openwebrx-panel-receiver").find(".openwebrx-modes").html(html);
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
}