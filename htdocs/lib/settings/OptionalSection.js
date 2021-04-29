$.fn.optionalSection = function(){
    this.each(function() {
        var $section = $(this);
        var $select = $section.find('.optional-select');
        var $optionalInputs = $section.find('.optional-inputs');
        $section.on('click', '.option-add-button', function(e){
            var field = $select.val();
            var group = $optionalInputs.find(".form-group[data-field='" + field + "']");
            group.find('input, select').filter(function(){
                // exclude template inputs
                return !$(this).parents('.template').length;
            }).prop('disabled', false);
            $section.find('hr').before(group);
            $select.find('option[value=\'' + field + '\']').remove();

            return false;
        });
        $section.on('click', '.option-remove-button', function(e) {
            var group = $(e.target).parents('.form-group')
            group.find('input, select').prop('disabled', true);
            $optionalInputs.append(group);
            var $label = group.find('label');
            var $option = $('<option value="' + group.data('field') + '">' + $label.text() + '</option>');
            $select.append($option);

            return false;
        })
    });
}