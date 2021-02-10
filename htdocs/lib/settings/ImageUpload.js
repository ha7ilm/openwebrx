$.fn.imageUpload = function() {
    $.each(this, function(){
        var $uploadButton = $(this).find('button.upload');
        var $restoreButton = $(this).find('button.restore');
        var $img = $(this).find('img');
        var originalUrl = $img.prop('src');
        var $input = $(this).find('input');
        var id = $input.prop('id');
        $uploadButton.click(function(){
            $uploadButton.prop('disabled', true);
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
                        $input.val(data.file);
                        $img.prop('src', '/imageupload?file=' + data.file);
                    }).always(function(){
                        $uploadButton.prop('disabled', false);
                    });
                }
            };

            input.click();
            return false;
        });

        $restoreButton.click(function(){
            $input.val('restore');
            $img.prop('src', originalUrl + "&mapped=false");
            return false;
        });
    });
}