from unittest import TestCase
from owrx.property.validators import OrValidator, IntegerValidator, StringValidator


class OrValidatorTest(TestCase):
    def testPassesAnyValidators(self):
        validator = OrValidator(IntegerValidator(), StringValidator())
        self.assertTrue(validator.isValid(42))
        self.assertTrue(validator.isValid("text"))

    def testRejectsOtherTypes(self):
        validator = OrValidator(IntegerValidator(), StringValidator())
        self.assertFalse(validator.isValid(.5))

    def testRejectsIfNoValidator(self):
        validator = OrValidator()
        self.assertFalse(validator.isValid("any value"))
