from unittest import TestCase
from owrx.property import PropertyLayer, PropertyReadOnly, PropertyWriteError


class PropertyReadOnlyTest(TestCase):
    def testPreventsWrites(self):
        layer = PropertyLayer()
        layer["testkey"] = "initial value"
        ro = PropertyReadOnly(layer)
        with self.assertRaises(PropertyWriteError):
            ro["testkey"] = "new value"
        with self.assertRaises(PropertyWriteError):
            ro["otherkey"] = "testvalue"
        self.assertEqual(ro["testkey"], "initial value")
        self.assertNotIn("otherkey", ro)
