from unittest import TestCase
from unittest.mock import Mock
from owrx.property.validators import LambdaValidator


class LambdaValidatorTest(TestCase):
    def testPassesValue(self):
        mock = Mock()
        validator = LambdaValidator(mock.method)
        validator.isValid("test")
        mock.method.assert_called_once_with("test")

    def testReturnsTrue(self):
        validator = LambdaValidator(lambda x: True)
        self.assertTrue(validator.isValid("any value"))
        self.assertTrue(validator.isValid(3.1415926))

    def testReturnsFalse(self):
        validator = LambdaValidator(lambda x: False)
        self.assertFalse(validator.isValid("any value"))
        self.assertFalse(validator.isValid(42))
