from unittest import TestCase
from owrx.property.validators import FloatValidator


class FloatValidatorTest(TestCase):
    def testPassesNumbers(self):
        validator = FloatValidator()
        self.assertTrue(validator.isValid(.5))

    def testDoesntPassOthers(self):
        validator = FloatValidator()
        self.assertFalse(validator.isValid(123))
        self.assertFalse(validator.isValid(-2))
        self.assertFalse(validator.isValid("text"))
        self.assertFalse(validator.isValid(object()))
