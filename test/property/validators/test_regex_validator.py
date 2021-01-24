from unittest import TestCase
from owrx.property.validators import RegexValidator
import re


class RegexValidatorTest(TestCase):
    def testMatchesRegex(self):
        validator = RegexValidator(re.compile("abc"))
        self.assertTrue(validator.isValid("abc"))

    def testDoesntMatchRegex(self):
        validator = RegexValidator(re.compile("abc"))
        self.assertFalse(validator.isValid("xyz"))

    def testFailsIfValueIsNoString(self):
        validator = RegexValidator(re.compile("abc"))
        self.assertFalse(validator.isValid(42))
