$.fn.exponentialInput = function() {
    var prefixes = {
        'K': 3,
        'M': 6,
        'G': 9,
        'T': 12
    };

    this.each(function(){
        var $group = $(this);
        var currentExponent = 0;
        var $input = $group.find('input');

        var setExponent = function() {
            var newExponent = parseInt($exponent.val());
            var delta = currentExponent - newExponent;
            if (delta >= 0) {
                $input.val(parseFloat($input.val()) * 10 ** delta);
            } else {
                // should not be necessary to handle this separately, but floating point precision in javascript
                // does not handle this well otherwise
                $input.val(parseFloat($input.val()) / 10 ** -delta);
            }
            currentExponent = newExponent;
        };

        $input.on('keydown', function(e) {
            var c = String.fromCharCode(e.which);
            if (c in prefixes) {
                currentExponent = prefixes[c];
                $exponent.val(prefixes[c]);
            }
        });

        var $exponent = $group.find('select.exponent');
        $exponent.on('change', setExponent);

        // calculate initial exponent
        var value = parseFloat($input.val());
        if (!Number.isNaN(value)) {
            $exponent.val(Math.floor(Math.log10(Math.abs(value)) / 3) * 3);
            setExponent();
        }
    })
};