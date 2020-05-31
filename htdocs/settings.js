function Input(name, value, options) {
    this.name = name;
    this.value = value;
    this.options = options;
    this.label = options && options.label || name;
};

Input.prototype.getClasses = function() {
    return ['form-control', 'form-control-sm'];
}

Input.prototype.bootstrapify = function(input) {
    this.getClasses().forEach(input.addClass.bind(input));
    return [
        '<div class="form-group row">',
            '<label class="col-form-label col-form-label-sm col-3" for="' + this.name + '">' + this.label + '</label>',
            '<div class="col-9">',
                $.map(input, function(el) {
                    return el.outerHTML;
                }).join(''),
            '</div>',
        '</div>'
    ].join('');
};

function TextInput() {
    Input.apply(this, arguments);
};

TextInput.prototype = new Input();

TextInput.prototype.render = function() {
    return this.bootstrapify($('<input type="text" name="' + this.name + '" value="' + this.value + '">'));
}

function NumberInput() {
    Input.apply(this, arguments);
};

NumberInput.prototype = new Input();

NumberInput.prototype.render = function() {
    return this.bootstrapify($('<input type="number" name="' + this.name + '" value="' + this.value + '">'));
};

function SoapyGainInput() {
    Input.apply(this, arguments);
}

SoapyGainInput.prototype = new Input();

SoapyGainInput.prototype.getClasses = function() {
    return [];
};

SoapyGainInput.prototype.render = function(){
    var markup = $(
        '<div class="row form-group">' +
            '<div class="col-4">Gain mode</div>' +
            '<div class="col-8">' +
                '<select class="form-control form-control-sm">' +
                    '<option value="auto">automatic gain</option>' +
                    '<option value="single">single gain value</option>' +
                    '<option value="separate">separate gain values</option>' +
                '</select>' +
            '</div>' +
        '</div>' +
        '<div class="row option form-group gain-mode-single">' +
            '<div class="col-4">Gain</div>' +
            '<div class="col-8">' +
                '<input class="form-control form-control-sm" type="number">' +
            '</div>' +
        '</div>' +
        this.options.gains.map(function(g){
            return '<div class="row option form-group gain-mode-separate">' +
                '<div class="col-4">' + g + '</div>' +
                '<div class="col-8">' +
                    '<input class="form-control form-control-sm" type="number">' +
                '</div>' +
            '</div>';
        }).join('')
    );
    var el = $(this.bootstrapify(markup))
    var setMode = function(mode){
        el.find('.option').hide();
        el.find('.gain-mode-' + mode).show();
    };
    el.on('change', 'select', function(){
        var mode = $(this).val();
        setMode(mode);
    });
    setMode('auto');
    return el;
};

function ProfileInput() {
    Input.apply(this, arguments);
};

ProfileInput.prototype = new Input();

ProfileInput.prototype.render = function() {
    return $('<div><h3>Profiles</h3></div>');
};

function SchedulerInput() {
    Input.apply(this, arguments);
};

SchedulerInput.prototype = new Input();

SchedulerInput.prototype.render = function() {
    return $('<div><h3>Scheduler</h3></div>');
};

function SdrDevice(el, data) {
    this.el = el;
    this.data = data;
    this.inputs = {};
    this.render();

    var self = this;
    el.on('click', '.fieldselector .btn', function() {
        var key = el.find('.fieldselector select').val();
        self.data[key] = self.getInitialValue(key);
        self.render();
    });
};

SdrDevice.create = function(el) {
    var data = JSON.parse(decodeURIComponent(el.data('config')));
    var type = data.type;
    var constructor = SdrDevice.types[type] || SdrDevice;
    return new constructor(el, data);
};

SdrDevice.prototype.getData = function() {
    return $.extend(new Object(), this.getDefaults(), this.data);
};

SdrDevice.prototype.getDefaults = function() {
    var defaults = {}
    $.each(this.getMappings(), function(k, v) {
        if (!v.includeInDefault) return;
        defaults[k] = 'initialValue' in v ? v['initialValue'] : false;
    });
    return defaults;
};

SdrDevice.prototype.getMappings = function() {
    return {
        "name": {
            constructor: TextInput,
            inputOptions: {
                label: "Name"
            },
            initialValue: "",
            includeInDefault: true
        },
        "type": {
            constructor: TextInput,
            inputOptions: {
                label: "Type"
            },
            initialValue: '',
            includeInDefault: true
        },
        "ppm": {
            constructor: NumberInput,
            inputOptions: {
                label: "PPM"
            },
            initialValue: 0
        },
        "profiles": {
            constructor: ProfileInput,
            inputOptions: {
                label: "Profiles"
            },
            initialValue: [],
            includeInDefault: true,
            position: 100
        },
        "scheduler": {
            constructor: SchedulerInput,
            inputOptions: {
                label: "Scheduler",
            },
            initialValue: {},
            position: 101
        },
        "rf_gain": {
            constructor: TextInput,
            inputOptions: {
                label: "Gain",
            },
            initialValue: 0
        }
    };
};

SdrDevice.prototype.getMapping = function(key) {
    var mappings = this.getMappings();
    return mappings[key];
};

SdrDevice.prototype.getInputClass = function(key) {
    var mapping = this.getMapping(key);
    return mapping && mapping.constructor || TextInput;
};

SdrDevice.prototype.getInitialValue = function(key) {
    var mapping = this.getMapping(key);
    return mapping && ('initialValue' in mapping) ? mapping['initialValue'] : false;
};

SdrDevice.prototype.getPosition = function(key) {
    var mapping = this.getMapping(key);
    return mapping && mapping.position || 10;
};

SdrDevice.prototype.getInputOptions = function(key) {
    var mapping = this.getMapping(key);
    return mapping && mapping.inputOptions || {};
};

SdrDevice.prototype.getLabel = function(key) {
    var options = this.getInputOptions(key);
    return options && options.label || key;
};

SdrDevice.prototype.render = function() {
    var self = this;
    self.el.empty();
    var data = this.getData();
    Object.keys(data).sort(function(a, b){
        return self.getPosition(a) - self.getPosition(b);
    }).forEach(function(key){
        var value = data[key];
        var inputClass = self.getInputClass(key);
        var input = new inputClass(key, value, self.getInputOptions(key));
        self.inputs[key] = input;
        self.el.append(input.render());
    });
    self.el.append(this.renderFieldSelector());
};

SdrDevice.prototype.renderFieldSelector = function() {
    var self = this;
    return '<div class="fieldselector">' +
        '<h3>Add new configuration options<h3>' +
        '<div class="form-group row">' +
            '<div class="col-3"><select class="form-control form-control-sm">' +
                Object.keys(self.getMappings()).filter(function(m){
                    return !(m in self.data);
                }).map(function(m) {
                    return '<option value="' + m + '">' + self.getLabel(m) + '</option>';
                }).join('') +
            '</select></div>' +
            '<div class="col-2">' +
                '<div class="btn btn-primary">Add to config</div>' +
            '</div>' +
        '</div>' +
    '</div>';
};

RtlSdrDevice = function() {
    SdrDevice.apply(this, arguments);
};

RtlSdrDevice.prototype = Object.create(SdrDevice.prototype);
RtlSdrDevice.prototype.constructor = RtlSdrDevice;

RtlSdrDevice.prototype.getMappings = function() {
    var mappings = SdrDevice.prototype.getMappings.apply(this, arguments);
    return $.extend(new Object(), mappings, {
        "device": {
            constructor: TextInput,
            inputOptions:{
                label: "Serial number"
            },
            initialValue: ""
        }
    });
};

SoapySdrDevice = function() {
    SdrDevice.apply(this, arguments);
};

SoapySdrDevice.prototype = Object.create(SdrDevice.prototype);
SoapySdrDevice.prototype.constructor = SoapySdrDevice;

SoapySdrDevice.prototype.getMappings = function() {
    var mappings = SdrDevice.prototype.getMappings.apply(this, arguments);
    return $.extend(new Object(), mappings, {
        "device": {
            constructor: TextInput,
            inputOptions:{
                label: "Soapy device selector"
            },
            initialValue: ""
        }
    });
};

SdrplaySdrDevice = function() {
    SoapySdrDevice.apply(this, arguments);
};

SdrplaySdrDevice.prototype = Object.create(SoapySdrDevice.prototype);
SdrplaySdrDevice.prototype.constructor = SdrplaySdrDevice;

SdrplaySdrDevice.prototype.getMappings = function() {
    var mappings = SoapySdrDevice.prototype.getMappings.apply(this, arguments);
    return $.extend(new Object(), mappings, {
        "rf_gain": {
            constructor: SoapyGainInput,
            initialValue: 0,
            inputOptions: {
                label: "Gain",
                gains: ['RFGR', 'IFGR']
            }
        }
    });
};

SdrDevice.types = {
    'rtl_sdr': RtlSdrDevice,
    'sdrplay': SdrplaySdrDevice
};

$.fn.sdrdevice = function() {
    return this.map(function(){
        var el = $(this);
        if (!el.data('sdrdevice')) {
            el.data('sdrdevice', SdrDevice.create(el));
        }
        return el.data('sdrdevice');
    });
};

$(function(){
    $(".map-input").each(function(el) {
        var $el = $(this);
        var field_id = $el.attr("for");
        var $lat = $('#' + field_id + '-lat');
        var $lon = $('#' + field_id + '-lon');
        $.getScript("https://maps.googleapis.com/maps/api/js?key=" + $el.data("key")).done(function(){
            $el.css("height", "200px");
            var lp = new locationPicker($el.get(0), {
                lat: parseFloat($lat.val()),
                lng: parseFloat($lon.val())
            }, {
                zoom: 7
            });

            google.maps.event.addListener(lp.map, 'idle', function(event){
                var pos = lp.getMarkerPosition();
                $lat.val(pos.lat);
                $lon.val(pos.lng);
            });
        });
    });

    $(".sdrdevice").sdrdevice();
});