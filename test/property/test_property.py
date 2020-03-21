import unittest
from owrx.property import Property


class PropertyTest(unittest.TestCase):
    def testSimple(self):
        prop = Property("testvalue")
        self.assertEqual(prop.getValue(), "testvalue")
