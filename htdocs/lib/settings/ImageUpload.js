$.fn.imageUpload = function() {
    $.each(this, function(){
        var $button = $(this).find('button');
        var $img = $(this).find('img');
        var $input = $(this).find('input');
        var id = $input.prop('id');
        $button.click(function(){
            $button.prop('disabled', true);
            var input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/jpeg, image/png';

            input.onchange = function(e) {
                var reader = new FileReader()
                // TODO: implement file size check
                reader.readAsArrayBuffer(e.target.files[0]);
                reader.onload = function(e) {
                    $.ajax({
                        url: '/imageupload?id=' + id,
                        type: 'POST',
                        data: e.target.result,
                        processData: false,
                        contentType: 'application/octet-stream',
                    }).done(function(data){
                        $input.val(data.uuid);
                        $img.prop('src', "/imageupload?id=" + id + "&uuid=" + data.uuid);
                    }).always(function(){
                        $button.prop('disabled', false);
                    });
                }
            };

            input.click();
            return false;
        });
    });
}