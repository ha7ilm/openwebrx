$.fn.logMessages = function() {
    $.each(this, function(){
        $(this).scrollTop(this.scrollHeight);
    });
};