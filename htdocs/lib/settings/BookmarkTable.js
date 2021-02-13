$.fn.bookmarktable = function() {
    $.each(this, function(){
        var $table = $(this);

        var inputs = $table.find('tr.inputs td').map(function(){
            var candidates = $(this).find('input, select')
            return candidates.length ? candidates.first() : false;
        }).toArray();
        $table.find('tr.inputs').remove();

        $table.on('dblclick', 'td', function(e) {
            var $cell = $(e.target);
            var html = $cell.html();

            var $row = $cell.parent('tr');
            var index = $row.find('td').index($cell);

            var $input = inputs[index];
            if (!$input) return;

            $input.val($cell.data('value') || html);
            $input.prop('disabled', false);
            $cell.html($input);
            $input.focus();

            var submit = function() {
                $input.prop('disabled', true);
                $.ajax(document.location.href + "/" + $row.data('id'), {
                    data: JSON.stringify(Object.fromEntries([[$input.prop('name'), $input.val()]])),
                    contentType: 'application/json',
                    method: 'POST'
                }).then(function(){
                    var $option = $input.find('option:selected')
                    if ($option.length) {
                        $cell.html($option.html());
                    } else {
                        $cell.html($input.val());
                    }
                });
            };

            $input.on('blur', submit).on('change', submit).on('keyup', function(e){
                if (e.keyCode == 13) return submit();
                if (e.keyCode == 27) {
                    $cell.html(html);
                }
            });
        });
    });
};
