from unittest import TestCase
from owrx.property.validators import IntegerValidator


class IntegerValidatorTest(TestCase):
    def testPassesIntegers(self):
        validator = IntegerValidator()
        self.assertTrue(validator.isValid(123))
        self.assertTrue(validator.isValid(-2))

    def testDoesntPassOthers(self):
        validator = IntegerValidator()
        self.assertFalse(validator.isValid(.5))
        self.assertFalse(validator.isValid("text"))
        self.assertFalse(validator.isValid(object()))
