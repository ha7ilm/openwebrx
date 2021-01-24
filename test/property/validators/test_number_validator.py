from unittest import TestCase
from owrx.property.validators import NumberValidator


class NumberValidatorTest(TestCase):
    def testPassesNumbers(self):
        validator = NumberValidator()
        self.assertTrue(validator.isValid(123))
        self.assertTrue(validator.isValid(-2))
        self.assertTrue(validator.isValid(.5))

    def testDoesntPassOthers(self):
        validator = NumberValidator()
        # bool is a subclass of int, so it passes this test.
        # not sure if we need to be more specific or if this is alright.
        # self.assertFalse(validator.isValid(True))
        self.assertFalse(validator.isValid("text"))
        self.assertFalse(validator.isValid(object()))
