from unittest import TestCase
from owrx.property import PropertyLayer, PropertyValidator, PropertyValidationError
from owrx.property.validators import NumberValidator, StringValidator


class PropertyValidatorTest(TestCase):
    def testPassesUnvalidated(self):
        pm = PropertyLayer()
        pv = PropertyValidator(pm)
        pv["testkey"] = "testvalue"
        self.assertEqual(pv["testkey"], "testvalue")
        self.assertEqual(pm["testkey"], "testvalue")

    def testPassesValidValue(self):
        pv = PropertyValidator(PropertyLayer(), {"testkey": NumberValidator()})
        pv["testkey"] = 42
        self.assertEqual(pv["testkey"], 42)

    def testThrowsErrorOnInvalidValue(self):
        pv = PropertyValidator(PropertyLayer(), {"testkey": NumberValidator()})
        with self.assertRaises(PropertyValidationError):
            pv["testkey"] = "text"

    def testSetValidator(self):
        pv = PropertyValidator(PropertyLayer())
        pv.setValidator("testkey", NumberValidator())
        with self.assertRaises(PropertyValidationError):
            pv["testkey"] = "text"

    def testUpdateValidator(self):
        pv = PropertyValidator(PropertyLayer(), {"testkey": StringValidator()})
        # this should pass
        pv["testkey"] = "text"
        pv.setValidator("testkey", NumberValidator())
        # this should raise
        with self.assertRaises(PropertyValidationError):
            pv["testkey"] = "text"
