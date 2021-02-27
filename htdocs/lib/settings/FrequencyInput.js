$.fn.frequencyInput = function() {
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

        $exponent = $group.find('select.frequency-exponent');
        $exponent.on('change', setExponent);

        // calculate initial exponent
        $exponent.val(Math.floor(Math.log10($input.val()) / 3) * 3);
        setExponent();
    })
};