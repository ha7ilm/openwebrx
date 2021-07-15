from unittest import TestCase
from owrx.property.validators import BoolValidator


class NumberValidatorTest(TestCase):
    def testPassesNumbers(self):
        validator = BoolValidator()
        self.assertTrue(validator.isValid(True))
        self.assertTrue(validator.isValid(False))

    def testDoesntPassOthers(self):
        validator = BoolValidator()
        self.assertFalse(validator.isValid(123))
        self.assertFalse(validator.isValid(-2))
        self.assertFalse(validator.isValid(.5))
        self.assertFalse(validator.isValid("text"))
        self.assertFalse(validator.isValid(object()))
