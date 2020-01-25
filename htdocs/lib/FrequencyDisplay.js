function FrequencyDisplay(element) {
    this.element = $(element);
    this.digits = [];
    this.displayContainer = $('<div>');
    this.digitContainer = $('<span>');
    this.displayContainer.html([this.digitContainer, $('<span> MHz</span>')]);
    this.element.html(this.displayContainer);
    this.decimalSeparator = (0.1).toLocaleString().substring(1, 2);
    this.setFrequency(0);
}

FrequencyDisplay.prototype.setFrequency = function(freq) {
    this.frequency = freq;
    var formatted = (freq / 1e6).toLocaleString(undefined, {maximumFractionDigits: 4, minimumFractionDigits: 4});
    var children = this.digitContainer.children();
    for (var i = 0; i < formatted.length; i++) {
        if (!this.digits[i]) {
            this.digits[i] = $('<span>');
            var before = children[i];
            if (before) {
                $(before).after(this.digits[i]);
            } else {
                this.digitContainer.append(this.digits[i]);
            }
        }
        this.digits[i][(isNaN(formatted[i]) ? 'remove' : 'add') + 'Class']('digit');
        this.digits[i].html(formatted[i]);
    }
    while (this.digits.length > formatted.length) {
        this.digits.pop().remove();
    }
};

function TuneableFrequencyDisplay(element) {
    FrequencyDisplay.call(this, element);
    this.setupEvents();
}

TuneableFrequencyDisplay.prototype = new FrequencyDisplay();

TuneableFrequencyDisplay.prototype.setupEvents = function() {
    var me = this;
    me.element.on('wheel', function(e){
        e.preventDefault();
        e.stopPropagation();

        var index = me.digitContainer.find('.digit').index(e.target);
        if (index < 0) return;

        var delta = 10 ** (Math.floor(Math.log10(me.frequency)) - index);
        if (e.originalEvent.deltaY > 0) delta *= -1;
        var newFrequency = me.frequency + delta;

        me.listeners.forEach(function(l) {
            l(newFrequency);
        });
    });
    me.listeners = [];
    me.element.on('click', function(){
        var input = $('<input>');
        var submit = function(){
            var freq = parseInt(input.val());
            if (!isNaN(freq)) {
                me.listeners.forEach(function(l) {
                    l(freq);
                });
            }
            input.remove();
            me.displayContainer.show();
        };
        input.on('blur', submit).on('keyup', function(e){
            if (e.keyCode == 13) return submit();
        });
        input.on('click', function(e){
            e.stopPropagation();
        });
        input.val(me.frequency);
        me.displayContainer.hide();
        me.element.append(input);
        input.focus();
    });
};

TuneableFrequencyDisplay.prototype.onFrequencyChange = function(listener){
    this.listeners.push(listener);
};