$.fn.waterfallDropdown = function(){
    this.each(function(){
        var $select = $(this);
        var setVisibility = function() {
            var show = $select.val() === 'CUSTOM';
            $('#waterfall_colors').parents('.form-group')[show ? 'show' : 'hide']();
        }
        $select.on('change', setVisibility);
        setVisibility();
    })
}