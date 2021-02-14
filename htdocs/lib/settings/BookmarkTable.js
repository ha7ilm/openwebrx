$.fn.bookmarktable = function() {
    $.each(this, function(){
        var $table = $(this).find('table');

        var inputs = $table.find('tr.inputs td').map(function(){
            var candidates = $(this).find('input, select')
            return candidates.length ? candidates.first() : false;
        }).toArray();
        $table.find('tr.inputs').remove();

        var transformToHtml = function($cell) {
            var $input = $cell.find('input, select');
            var $option = $input.find('option:selected')
            if ($option.length) {
                $cell.html($option.html());
            } else {
                $cell.html($input.val());
            }
        };

        $table.on('dblclick', 'td', function(e) {
            var $cell = $(e.target);
            var html = $cell.html();

            var $row = $cell.parent('tr');
            var index = $row.find('td').index($cell);

            var $input = inputs[index];
            if (!$input) return;

            $table.find('tr[data-id="new"]').remove();
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
                    transformToHtml($cell);
                });
            };

            $input.on('blur', submit).on('change', submit).on('keyup', function(e){
                if (e.keyCode == 13) return submit();
                if (e.keyCode == 27) {
                    $cell.html(html);
                }
            });
        });

        $(this).find('.bookmark-add').on('click', function() {
            if ($table.find('tr[data-id="new"]').length) return;

            var row = $('<tr data-id="new">');
            row.append(inputs.map(function(i){
                var cell = $('<td>');
                if (i) {
                    i.prop('disabled', false);
                    i.val('');
                    cell.html(i);
                } else {
                    cell.html(
                        '<div class="btn-group btn-group-sm">' +
                            '<button class="btn btn-primary bookmark-save">Save</button>' +
                            '<button class="btn btn-secondary bookmark-cancel">Cancel</button>' +
                        '</div>'
                    );
                }
                return cell;
            }));

            row.on('click', '.bookmark-cancel', function() {
                row.remove();
            });

            row.on('click', '.bookmark-save', function() {
                var data = Object.fromEntries(
                    row.find('input, select').toArray().map(function(input){
                        var $input = $(input);
                        $input.prop('disabled', true);
                        return [$input.prop('name'), $input.val()]
                    })
                );

                $.ajax(document.location.href, {
                    data: JSON.stringify(data),
                    contentType: 'application/json',
                    method: 'POST'
                }).then(function(data){
                    if ('bookmark_id' in data) {
                        row.attr('data-id', data['bookmark_id']);
                        row.find('td').each(function(){
                            var $cell = $(this);
                            var $group = $cell.find('.btn-group')
                            if ($group.length) {
                                $group.remove;
                                $cell.html('<div class="btn btn-sm btn-danger bookmark-delete">delete</div>');
                            }
                            transformToHtml($cell);
                        });
                    }
                });

            });

            $table.append(row);
            row[0].scrollIntoView();
        });
    });
};
