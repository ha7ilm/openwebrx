$.fn.wsjtDecodingDepthsInput = function() {
    var renderTable = function(data) {
        var $table = $('<table class="table table-sm table-borderless wsjt-decoding-depths-table">');
        $table.append($.map(data, function(value, mode){
            return $('<tr><td>' + mode + '</td><td>' + value + '</td></tr>');
        }));
        return $table;
    }

    this.each(function(){
        var $input = $(this);
        var $el = $input.parent();
        var $table = renderTable(JSON.parse($input.val()));
        $el.append($table);
    });
};