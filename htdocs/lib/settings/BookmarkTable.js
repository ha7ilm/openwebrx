function Editor(table) {
    this.table = table;
}

Editor.prototype.getInputHtml = function() {
    return '<input>';
}

Editor.prototype.render = function(el) {
    this.input = $(this.getInputHtml());
    el.append(this.input);
    this.setupEvents();
};

Editor.prototype.setupEvents = function() {
    var me = this;
    this.input.on('blur', function() { me.submit(); }).on('change', function() { me.submit(); }).on('keydown', function(e){
        if (e.keyCode == 13) return me.submit();
        if (e.keyCode == 27) return me.cancel();
    });
};

Editor.prototype.submit = function() {
    if (!this.onSubmit) return;
    var submit = this.onSubmit;
    delete this.onSubmit;
    submit();
};

Editor.prototype.cancel = function() {
    if (!this.onCancel) return;
    var cancel = this.onCancel;
    delete this.onCancel;
    cancel();
};

Editor.prototype.focus = function() {
    this.input.focus();
};

Editor.prototype.disable = function(flag) {
    this.input.prop('disabled', flag);
};

Editor.prototype.setValue = function(value) {
    this.input.val(value);
};

Editor.prototype.getValue = function() {
    return this.input.val();
};

Editor.prototype.getHtml = function() {
    return this.getValue();
};

function NameEditor(table) {
    Editor.call(this, table);
}

NameEditor.prototype = new Editor();

NameEditor.prototype.getInputHtml = function() {
    return '<input class="form-control form-control-sm" type="text">';
}

function FrequencyEditor(table) {
    Editor.call(this, table);
}

FrequencyEditor.suffixes = {
    '': 0,
    'K': 3,
    'M': 6,
    'G': 9,
    'T': 12
};

FrequencyEditor.prototype = new Editor();

FrequencyEditor.prototype.getInputHtml = function() {
    return '<div class="input-group input-group-sm exponential-input" name="frequency">' +
        '<input class="form-control form-control-sm" type="number" step="1">' +
        '<div class="input-group-append">' +
            '<select class="input-group-text exponent">' +
                $.map(FrequencyEditor.suffixes, function(v, k) {
                    // fix lowercase "kHz"
                    if (k === "K") k = "k";
                    return '<option value="' + v + '">' + k + 'Hz</option>';
                }).join('') +
            '</select>' +
        '</div>' +
    '</div>';
};

FrequencyEditor.prototype.render = function(el) {
    this.input = $(this.getInputHtml());
    el.append(this.input);
    this.freqInput = el.find('input');
    this.expInput = el.find('select');
    this.setupEvents();
};

FrequencyEditor.prototype.setupEvents = function() {
    var me = this;
    var inputs = [this.freqInput, this.expInput].map(function(i) { return i[0]; });
    inputs.forEach(function(input) {
        $(input).on('blur', function(e){
            if (inputs.indexOf(e.relatedTarget) >= 0) {
                return;
            }
            me.submit();
        });
    });

    var me = this;
    this.freqInput.on('keydown', function(e){
        if (e.keyCode == 13) return me.submit();
        if (e.keyCode == 27) return me.cancel();
        var c = String.fromCharCode(e.which);
        if (c in FrequencyEditor.suffixes) {
            me.expInput.val(FrequencyEditor.suffixes[c]);
        }
    });
}

FrequencyEditor.prototype.getValue = function() {
    var frequency = parseFloat(this.freqInput.val());
    var exp = parseInt(this.expInput.val());
    return Math.floor(frequency * 10 ** exp);
};

FrequencyEditor.prototype.setValue = function(value) {
    var value = parseFloat(value);
    var exp = 0;
    if (!Number.isNaN(value) && value > 0) {
        exp = Math.floor(Math.log10(value) / 3) * 3;
    }
    this.freqInput.val(value / 10 ** exp);
    this.expInput.val(exp);
};

FrequencyEditor.prototype.focus = function() {
    this.freqInput.focus();
};

var renderFrequency = function(freq) {
    var exp = 0;
    if (!Number.isNaN(freq)) {
        exp = Math.floor(Math.log10(freq) / 3) * 3;
    }
    var frequency = freq / 10 ** exp;
    var suffix = Object.entries(FrequencyEditor.suffixes).find(function(e) {
        return e[1] == exp;
    });
    if (!suffix) {
        return freq + ' Hz';
    }
    // fix lowercase 'kHz'
    suffix = suffix[0] == 'K' ? 'k' : suffix[0];
    var expString = suffix[0] + 'Hz';
    return frequency + ' ' + expString;
}

FrequencyEditor.prototype.getHtml = function() {
    return renderFrequency(this.getValue());
};

function ModulationEditor(table) {
    Editor.call(this, table);
    this.modes = table.data('modes');
}

ModulationEditor.prototype = new Editor();

ModulationEditor.prototype.getInputHtml = function() {
    return '<select class="form-control form-control-sm">' +
        $.map(this.modes, function(name, modulation) {
            return '<option value="' + modulation + '">' + name + '</option>';
        }).join('') +
        '</select>';
};

ModulationEditor.prototype.getHtml = function() {
    var $option = this.input.find('option:selected')
    return $option.html();
};

$.fn.bookmarktable = function() {
    var editors = {
        name: NameEditor,
        frequency: FrequencyEditor,
        modulation: ModulationEditor
    };

    $.each(this, function(){
        var $table = $(this).find('table');

        $table.on('dblclick', 'td', function(e) {
            var $cell = $(e.target);
            var html = $cell.html();

            var $row = $cell.parents('tr');
            var name = $cell.data('editor');
            var EditorCls = editors[name];
            if (!EditorCls) return;

            var editor = new EditorCls($table);
            editor.render($cell.html(''));
            editor.setValue($cell.data('value'));
            editor.focus();

            editor.onSubmit = function() {
                editor.disable(true);
                $.ajax(document.location.href + "/" + $row.data('id'), {
                    data: JSON.stringify(Object.fromEntries([[name, editor.getValue()]])),
                    contentType: 'application/json',
                    method: 'POST'
                }).done(function(){
                    $cell.data('value', editor.getValue());
                    $cell.html(editor.getHtml());
                });
            };

            editor.onCancel = function() {
                $cell.html(html);
            };
        });

        var $modal = $('#deleteModal').modal({show:false});

        $modal.on('hidden.bs.modal', function() {
            var $row = $modal.data('row');
            if (!$row) return;
            $row.find('.bookmark-delete').prop('disabled', false);
            $modal.removeData('row');
        });

        $modal.on('click', '.confirm', function() {
            var $row = $modal.data('row');
            if (!$row) return;
            $.ajax(document.location.href + "/" + $row.data('id'), {
                data: "{}",
                contentType: 'application/json',
                method: 'DELETE'
            }).done(function(){
                $row.remove();
                $modal.modal('hide');
            });
        });

        $table.on('click', '.bookmark-delete', function(e) {
            var $button = $(e.target);
            $button.prop('disabled', true);

            var $row = $button.parents('tr');
            $modal.data('row', $row);
            $modal.modal('show');
        });

        $(this).on('click', '.bookmark-add', function() {
            if ($table.find('tr[data-id="new"]').length) return;

            var row = $('<tr data-id="new">');

            var inputs = Object.fromEntries(
                Object.entries(editors).map(function(e) {
                    return [e[0], new e[1]($table)];
                })
            );

            row.append($.map(inputs, function(editor, name){
                var cell = $('<td data-editor="' + name + '" class="' + name + '">');
                editor.render(cell);
                return cell;
            }));
            row.append($(
                '<td>' +
                    '<div class="btn-group btn-group-sm">' +
                        '<button type="button" class="btn btn-primary bookmark-save">Save</button>' +
                        '<button type="button" class="btn btn-secondary bookmark-cancel">Cancel</button>' +
                    '</div>' +
                '</td>'
            ));

            row.on('click', '.bookmark-cancel', function() {
                row.remove();
            });

            row.on('click', '.bookmark-save', function() {
                var data = Object.fromEntries(
                    $.map(inputs, function(input, name){
                        input.disable(true);
                        // double wrapped because jQuery.map() flattens the result
                        return [[name, input.getValue()]];
                    })
                );

                $.ajax(document.location.href, {
                    data: JSON.stringify([data]),
                    contentType: 'application/json',
                    method: 'POST'
                }).done(function(data){
                    if (data.length && data.length === 1 && 'bookmark_id' in data[0]) {
                        row.attr('data-id', data[0]['bookmark_id']);
                        var tds = row.find('td');

                        Object.values(inputs).forEach(function(input, index) {
                            var td = $(tds[index]);
                            td.data('value', input.getValue());
                            td.html(input.getHtml());
                        });

                        var $cell = row.find('td').last();
                        var $group = $cell.find('.btn-group');
                        if ($group.length) {
                            $group.remove;
                            $cell.html('<div class="btn btn-sm btn-danger bookmark-delete">delete</div>');
                        }
                    }
                });

            });

            $table.append(row);
            row[0].scrollIntoView();
        });

        var $importModal = $('#importModal').modal({show: false});

        $(this).find('.bookmark-import').on('click', function() {
            var storage = new BookmarkLocalStorage();
            var bookmarks = storage.getBookmarks();
            if (bookmarks.length) {
                var modes = $table.data('modes');
                var $list = $('<table class="table table-sm">');
                $list.append(bookmarks.map(function(b) {
                    var modulation = b.modulation;
                    if (modulation in modes) {
                        modulation = modes[modulation];
                    }
                    var row = $(
                        '<tr>' +
                            '<td><input class="form-check-input select" type="checkbox"></td>' +
                            '<td>' + b.name + '</td>' +
                            '<td class="frequency">' + renderFrequency(b.frequency) + '</td>' +
                            '<td>' + modulation + '</td>' +
                        '</tr>'
                    );
                    row.data('bookmark', b);
                    return row;
                }));
                $importModal.find('.bookmark-list').html($list);
            } else {
                $importModal.find('.bookmark-list').html('No personal bookmarks found in this browser');
            }
            $importModal.modal('show');
        });

        $importModal.on('click', '.confirm', function() {
            var $list = $importModal.find('.bookmark-list table');
            if ($list.length) {
                var selected = $list.find('tr').filter(function(){
                    return $(this).find('.select').is(':checked');
                }).map(function(){
                    return $(this).data('bookmark');
                }).toArray();
                if (selected.length) {
                    $.ajax(document.location.href, {
                        data: JSON.stringify(selected),
                        contentType: 'application/json',
                        method: 'POST'
                    }).done(function(data){
                        var modes = $table.data('modes');
                        if (data.length && data.length == selected.length) {
                            $table.append(data.map(function(obj, index) {
                                var bookmark = selected[index];
                                var modulation_name = bookmark.modulation;
                                if (modulation_name in modes) {
                                    modulation_name = modes[modulation_name];
                                }
                                return $(
                                    '<tr data-id="' + obj.bookmark_id + '">' +
                                        '<td data-editor="name" data-value="' + bookmark.name + '">' + bookmark.name + '</td>' +
                                        '<td data-editor="frequency" data-value="' + bookmark.frequency + '" class="frequency">' + renderFrequency(bookmark.frequency) +'</td>' +
                                        '<td data-editor="modulation" data-value="' + bookmark.modulation + '">' + modulation_name + '</td>' +
                                        '<td>' +
                                            '<button type="button" class="btn btn-sm btn-danger bookmark-delete">delete</button>' +
                                        '</td>' +
                                    '</tr>'
                                )
                            }));
                        }
                    });
                }
            }
            $importModal.modal('hide');
        });
    });
};
