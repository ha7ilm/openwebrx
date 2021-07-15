$.fn.gainInput = function() {
    this.each(function() {
        var $container = $(this);

        var update = function(value){
            $container.find('.option').hide();
            $container.find('.option.' + value).show();
        }

        var $select = $container.find('select');
        $select.on('change', function(e) {
            var value = $(e.target).val();
            update(value);
        });
        update($select.val());
    });
}