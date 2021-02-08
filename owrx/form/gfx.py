from owrx.form import Input


class AvatarInput(Input):
    def __init__(self, id, label, infotext=None):
        super().__init__(id, label, infotext=infotext)

    def render_input(self, value):
        return """
            <div class="imageupload">
                <input type="hidden" id="{id}" name="{id}">
                <img class="webrx-rx-avatar" src="static/gfx/openwebrx-avatar.png" alt="Receiver avatar"/>
                <button class="btn btn-primary">Upload new image...</button>
            </div>
        """.format(
            id=self.id
        )
