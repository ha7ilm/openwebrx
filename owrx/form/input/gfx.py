from abc import ABCMeta, abstractmethod
from owrx.form.input import Input
from datetime import datetime


class ImageInput(Input, metaclass=ABCMeta):
    def render_input(self, value, errors):
        # TODO display errors
        return """
            <div class="imageupload">
                <input type="hidden" id="{id}" name="{id}">
                <div class="image-container">
                    <img class="{classes}" src="{url}" alt="{label}"/>
                </div>
                <button type="button" class="btn btn-primary upload">Upload new image...</button>
                <button type="button" class="btn btn-secondary restore">Restore original image</button>
            </div>
        """.format(
            id=self.id, label=self.label, url=self.cachebuster(self.getUrl()), classes=" ".join(self.getImgClasses())
        )

    def cachebuster(self, url: str):
        return "{url}{separator}cb={cachebuster}".format(
            url=url,
            cachebuster=datetime.now().timestamp(),
            separator="&" if "?" in url else "?",
        )

    @abstractmethod
    def getUrl(self) -> str:
        pass

    @abstractmethod
    def getImgClasses(self) -> list:
        pass


class AvatarInput(ImageInput):
    def getUrl(self) -> str:
        return "../static/gfx/openwebrx-avatar.png"

    def getImgClasses(self) -> list:
        return ["webrx-rx-avatar"]


class TopPhotoInput(ImageInput):
    def getUrl(self) -> str:
        return "../static/gfx/openwebrx-top-photo.jpg"

    def getImgClasses(self) -> list:
        return ["webrx-top-photo"]
