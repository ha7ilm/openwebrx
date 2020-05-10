function Input(name, value) {
    this.name = name;
    this.value = value;
};

Input.prototype.bootstrapify = function(input, label) {
    input.addClass('form-control').addClass('form-control-sm');
    return [
        '<div class="form-group row">',
            '<label class="col-form-label col-form-label-sm col-3" for="' + self.name + '">' + this.name + '</label>',
            '<div class="col-9">',
                input[0].outerHTML,
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

Input.mappings = {
    "name": TextInput,
    "type": TextInput,
    "ppm": NumberInput,
    "profiles": ProfileInput,
    "scheduler": SchedulerInput
};

function SdrDevice(el) {
    this.el = el;
    this.data = JSON.parse(decodeURIComponent(el.data('config')));
    this.inputs = {};
    this.render();

    var self = this;
    el.on('click', '.fieldselector .btn', function() {
        var key = el.find('.fieldselector select').val();
        self.data[key] = false;
        self.render();
    });
};

SdrDevice.prototype.render = function() {
    var self = this;
    self.el.empty();
    $.each(this.data, function(key, value) {
        var inputClass = Input.mappings[key] || TextInput;
        var input = new inputClass(key, value);
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
                Object.keys(Input.mappings).filter(function(m){
                    return !(m in self.data);
                }).map(function(m) {
                    return '<option name="' + m + '">' + m + '</option>';
                }).join('') +
            '</select></div>' +
            '<div class="col-2">' +
                '<div class="btn btn-primary">Add to config</div>' +
            '</div>' +
        '</div>' +
    '</div>';
};

$.fn.sdrdevice = function() {
    return this.map(function(){
        var el = $(this);
        if (!el.data('sdrdevice')) {
            el.data('sdrdevice', new SdrDevice(el));
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