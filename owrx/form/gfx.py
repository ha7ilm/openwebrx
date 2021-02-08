from owrx.form import Input


class AvatarInput(Input):
    def render_input(self, value):
        return """
            <div class="imageupload">
                <input type="hidden" id="{id}" name="{id}">
                <div class="image-container">
                    <img class="webrx-rx-avatar" src="static/gfx/openwebrx-avatar.png" alt="Receiver avatar"/>
                </div>
                <button class="btn btn-primary">Upload new image...</button>
            </div>
        """.format(
            id=self.id
        )


class TopPhotoInput(Input):
    def render_input(self, value):
        return """
            <div class="imageupload">
                <input type="hidden" id="{id}" name="{id}">
                <div class="image-container">
                    <img class="webrx-top-photo" src="static/gfx/openwebrx-top-photo.jpg" alt="Receiver Panorama"/>
                </div>
                <button class="btn btn-primary">Upload new image...</button>
            </div>
        """.format(
            id=self.id
        )
