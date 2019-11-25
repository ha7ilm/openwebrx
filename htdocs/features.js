$(function(){
    var converter = new showdown.Converter();
    $.ajax('api/features').done(function(data){
        var $table = $('table.features');
        $.each(data, function(name, details) {
            var requirements = $.map(details.requirements, function(r, name){
                return '<tr>' +
                           '<td></td>' +
                           '<td>' + name + '</td>' +
                           '<td>' + converter.makeHtml(r.description) + '</td>' +
                           '<td>' + (r.available ? 'YES' : 'NO') + '</td>' +
                       '</tr>';
            });
            $table.append(
                '<tr>' +
                    '<td colspan=2>' + name + '</td>' +
                    '<td>' + converter.makeHtml(details.description) + '</td>' +
                    '<td>' + (details.available ? 'YES' : 'NO') + '</td>' +
                '</tr>' +
                requirements.join("")
            );
        })
    });
});
