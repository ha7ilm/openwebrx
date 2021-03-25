$.fn.wsjtDecodingDepthsInput = function() {
    function WsjtDecodingDepthRow(inputs, mode, value) {
        this.el = $('<tr>');
        this.modeInput = $(inputs.get(0)).clone();
        this.modeInput.val(mode);
        this.valueInput = $(inputs.get(1)).clone();
        this.valueInput.val(value);
        this.removeButton = $('<button type="button" class="btn btn-sm btn-danger remove">Remove</button>');
        this.removeButton.data('row', this);
        this.el.append([this.modeInput, this.valueInput, this.removeButton].map(function(i) {
            return $('<td>').append(i);
        }));
    }

    WsjtDecodingDepthRow.prototype.getEl = function() {
        return this.el;
    }

    WsjtDecodingDepthRow.prototype.getValue = function() {
        var value = parseInt(this.valueInput.val())
        if (Number.isNaN(value)) {
            return {};
        }
        return Object.fromEntries([[this.modeInput.val(), value]]);
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

        var updateValue = function(){
            $input.val(JSON.stringify($.extend.apply({}, rows.map(function(r) {
                return r.getValue();
            }))));
        };

        $table.on('change', updateValue);
        var $addButton = $('<button type="button" class="btn btn-sm btn-primary">Add...</button>');

        $addButton.on('click', function() {
            var row = new WsjtDecodingDepthRow(inputs)
            rows.push(row);
            $table.append(row.getEl());
            return false;
        });
        $el.on('click', '.btn.remove', function(e){
            var row = $(e.target).data('row');
            var index = rows.indexOf(row);
            if (index < 0) return false;
            rows.splice(index, 1);
            row.getEl().remove();
            updateValue();
            return false;
        });

        $input.after($table, $addButton);
    });
};