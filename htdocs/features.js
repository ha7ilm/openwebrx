$(function(){
    $.ajax('/api/features').done(function(data){
        $('body').html(JSON.stringify(data));
    });
});