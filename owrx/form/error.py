class FormError(Exception):
    def __init__(self, key, message):
        super().__init__("Error processing form data for {}: {}".format(key, message))
        self.key = key
        self.message = message

    def getKey(self):
        return self.key

    def getMessage(self):
        return self.message


class ValidationError(FormError):
    pass
