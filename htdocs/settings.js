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

Input.mappings = {
    "name": TextInput
};

function SdrDevice(el) {
    this.el = el;
    this.data = JSON.parse(decodeURIComponent(el.data('config')));
    this.inputs = {};
    this.render();
};

SdrDevice.prototype.render = function() {
    var self = this;
    $.each(this.data, function(key, value) {
        var inputClass = Input.mappings[key] || TextInput;
        var input = new inputClass(key, value);
        self.inputs[key] = input;
        self.el.append(input.render())
    });
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

    console.info($(".sdrdevice").sdrdevice());
});