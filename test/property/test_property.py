import unittest
from unittest.mock import Mock
from owrx.property import Property


class PropertyTest(unittest.TestCase):
    def testValue(self):
        prop = Property("testvalue")
        self.assertEqual(prop.getValue(), "testvalue")

    def testChangeValue(self):
        prop = Property("before")
        prop.setValue("after")
        self.assertEqual(prop.getValue(), "after")

    def testInitialValueOnCallback(self):
        prop = Property("before")
        m = Mock()
        prop.wire(m.method)
        m.method.assert_called_once_with("before")

    def testChangedValueOnCallback(self):
        prop = Property("before")
        m = Mock()
        prop.wire(m.method)
        m.reset_mock()
        prop.setValue("after")
        m.method.assert_called_with("after")
