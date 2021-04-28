function FrequencyDisplay(element) {
    this.suffixes = {
        '': 0,
        'k': 3,
        'M': 6,
        'G': 9,
        'T': 12
    };
    this.element = $(element);
    this.digits = [];
    this.precision = 2;
    this.setupElements();
    this.setFrequency(0);
}

FrequencyDisplay.prototype.setupElements = function() {
    this.displayContainer = $('<div>');
    this.digitContainer = $('<span>');
    this.unitContainer = $('<span> Hz</span>');
    this.displayContainer.html([this.digitContainer, this.unitContainer]);
    this.element.html(this.displayContainer);
};

FrequencyDisplay.prototype.getSuffix = function() {
    var me = this;
    return Object.keys(me.suffixes).filter(function(key){
        return me.suffixes[key] == me.exponent;
    })[0] || "";
};

FrequencyDisplay.prototype.setFrequency = function(freq) {
    this.frequency = freq;
    if (this.frequency === 0 || Number.isNaN(this.frequency)) {
        this.exponent = 0
    } else {
        this.exponent = Math.floor(Math.log10(this.frequency) / 3) * 3;
    }

    var digits = Math.max(0, this.exponent - this.precision);
    var formatted = (freq / 10 ** this.exponent).toLocaleString(
        undefined,
        {maximumFractionDigits: digits, minimumFractionDigits: digits}
    );
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
    this.unitContainer.text(' ' + this.getSuffix() + 'Hz');
};

FrequencyDisplay.prototype.setTuningPrecision = function(precision) {
    if (typeof(precision) == 'undefined') return;
    this.precision = precision;
    this.setFrequency(this.frequency);
};

function TuneableFrequencyDisplay(element) {
    FrequencyDisplay.call(this, element);
    this.setupEvents();
}

TuneableFrequencyDisplay.prototype = new FrequencyDisplay();

TuneableFrequencyDisplay.prototype.setupElements = function() {
    FrequencyDisplay.prototype.setupElements.call(this);
    this.input = $('<input>');
    this.suffixInput = $('<select tabindex="-1">');
    this.suffixInput.append($.map(this.suffixes, function(e, p) {
        return $('<option value="' + e + '">' + p + 'Hz</option>');
    }));
    this.inputGroup = $('<div class="input-group">');
    this.inputGroup.append([this.input, this.suffixInput]);
    this.inputGroup.hide();
    this.element.append(this.inputGroup);
};

TuneableFrequencyDisplay.prototype.setupEvents = function() {
    var me = this;

    me.displayContainer.on('wheel', function(e){
        e.preventDefault();
        e.stopPropagation();

        var index = me.digitContainer.find('.digit').index(e.target);
        if (index < 0) return;

        var delta = 10 ** (Math.floor(Math.max(me.exponent, Math.log10(me.frequency))) - index);
        if (e.originalEvent.deltaY > 0) delta *= -1;
        var newFrequency = me.frequency + delta;

        me.element.trigger('frequencychange', newFrequency);
    });

    var submit = function(){
        var exponent = parseInt(me.suffixInput.val());
        var freq = parseFloat(me.input.val()) * 10 ** exponent;
        if (!isNaN(freq)) {
            me.element.trigger('frequencychange', freq);
        }
        me.inputGroup.hide();
        me.displayContainer.show();
    };
    $inputs = $.merge($(), me.input);
    $inputs = $.merge($inputs, me.suffixInput);
    $('body').on('click', function(e) {
        if (!me.input.is(':visible')) return;
        if ($.contains(me.element[0], e.target)) return;
        submit();
    });
    $inputs.on('blur', function(e){
        if ($inputs.toArray().indexOf(e.relatedTarget) >= 0) {
            return;
        }
        submit();
    });
    me.input.on('keydown', function(e){
        if (e.keyCode == 13) return submit();
        if (e.keyCode == 27) {
            me.inputGroup.hide();
            me.displayContainer.show();
            return;
        }
        var c = String.fromCharCode(e.which);
        Object.entries(me.suffixes).forEach(function(e) {
            if (e[0].toUpperCase() == c) {
                me.suffixInput.val(e[1]);
                return submit();
            }
        })
    });
    var currentExponent;
    me.suffixInput.on('change', function() {
        var newExponent = me.suffixInput.val();
        delta = currentExponent - newExponent;
        if (delta >= 0) {
            me.input.val(parseFloat(me.input.val()) * 10 ** delta);
        } else {
            // should not be necessary to handle this separately, but floating point precision in javascript
            // does not handle this well otherwise
            me.input.val(parseFloat(me.input.val()) / 10 ** -delta);
        }
        currentExponent = newExponent;
        me.input.focus();
    });
    $inputs.on('click', function(e){
        e.stopPropagation();
    });
    me.element.on('click', function(){
        currentExponent = me.exponent;
        me.input.val(me.frequency / 10 ** me.exponent);
        me.suffixInput.val(me.exponent);
        me.inputGroup.show();
        me.displayContainer.hide();
        me.input.focus();
    });
};

$.fn.frequencyDisplay = function() {
    if (!this.data('frequencyDisplay')) {
        this.data('frequencyDisplay', new FrequencyDisplay(this));
    }
    return this.data('frequencyDisplay');
}

$.fn.tuneableFrequencyDisplay = function() {
    if (!this.data('frequencyDisplay')) {
        this.data('frequencyDisplay', new TuneableFrequencyDisplay(this));
    }
    return this.data('frequencyDisplay');
}
