$.fn.frequencyInput = function() {
    var suffixes = {
        "K": 3,
        "M": 6,
        "G": 9,
        "T": 12
    };

    this.each(function(){
        var $group = $(this);
        var currentExponent = 0;
        $input = $group.find('input');

        var setExponent = function() {
            var newExponent = parseInt($exponent.val());
            var delta = currentExponent - newExponent;
            $input.val(parseFloat($input.val()) * 10 ** delta);
            currentExponent = newExponent;
        };

        $input.on('keydown', function(e) {
            var c = String.fromCharCode(e.which);
            if (c in suffixes) {
                currentExponent = suffixes[c];
                $exponent.val(suffixes[c]);
            }
        });

        $exponent = $group.find('select.frequency-exponent');
        $exponent.on('change', setExponent);

        // calculate initial exponent
        var value = parseFloat($input.val());
        if (!Number.isNaN(value)) {
            $exponent.val(Math.floor(Math.log10(value) / 3) * 3);
            setExponent();
        }
    })
};