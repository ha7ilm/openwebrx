$.fn.wsjtDecodingDepthsInput = function() {
    function WsjtDecodingDepthRow(inputs, mode, value) {
        this.el = $('<tr>');
        this.modeInput = $(inputs.get(0)).clone();
        this.modeInput.val(mode);
        this.valueInput = $(inputs.get(1)).clone();
        this.valueInput.val(value);
        this.el.append([this.modeInput, this.valueInput].map(function(i) {
            return $('<td>').append(i);
        }));
    }

    WsjtDecodingDepthRow.prototype.getEl = function() {
        return this.el;
    }

    this.each(function(){
        var $input = $(this);
        var $el = $input.parent();
        var $inputs = $el.find('.inputs')
        var inputs = $inputs.find('input, select');
        $inputs.remove();
        var rows = $.map(JSON.parse($input.val()), function(value, mode) {
            return new WsjtDecodingDepthRow(inputs, mode, value);
        });
        var $table = $('<table class="table table-sm table-borderless wsjt-decoding-depths-table">');
        $table.append(rows.map(function(r) {
            return r.getEl();
        }));
        $el.append($table);
    });
};