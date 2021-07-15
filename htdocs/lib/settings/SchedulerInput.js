$.fn.schedulerInput = function() {
    this.each(function() {
        var $container = $(this);
        var $template = $container.find('.template');
        $template.find('input, select').prop('disabled', true);

        var update = function(value){
            $container.find('.option').hide();
            $container.find('.option.' + value).show();
        }

        var $select = $container.find('select.mode');
        $select.on('change', function(e) {
            var value = $(e.target).val();
            update(value);
        });
        update($select.val());

        $container.find('.add-button').on('click', function() {
            var row = $template.clone();
            row.removeClass('template').show();
            row.find('input, select').prop('disabled', false);
            $template.before(row);

            return false;
        });

        $container.on('click', '.remove-button', function(e) {
            var row = $(e.target).parents('.scheduler-static-time-inputs');
            row.remove();
        });
    });
}