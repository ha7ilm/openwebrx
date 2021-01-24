from unittest import TestCase
from owrx.property.validators import StringValidator

class StringValidatorTest(TestCase):
    def testPassesStrings(self):
        validator = StringValidator()
        self.assertTrue(validator.isValid("text"))

    def testDoesntPassOthers(self):
        validator = StringValidator()
        self.assertFalse(validator.isValid(123))
        self.assertFalse(validator.isValid(-2))
        self.assertFalse(validator.isValid(.5))
        self.assertFalse(validator.isValid(object()))
