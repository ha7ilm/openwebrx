from unittest import TestCase
from owrx.property.validators import Validator, NumberValidator, LambdaValidator, StringValidator


class ValidatorTest(TestCase):

    def testReturnsValidator(self):
        validator = NumberValidator()
        self.assertIs(validator, Validator.of(validator))

    def testTransformsLambda(self):
        def my_callable(v):
            return True
        validator = Validator.of(my_callable)
        self.assertIsInstance(validator, LambdaValidator)
        self.assertTrue(validator.isValid("test"))

    def testGetsValidatorByKey(self):
        validator = Validator.of("str")
        self.assertIsInstance(validator, StringValidator)
