from unittest import TestCase
from unittest.mock import Mock
from owrx.property import PropertyLayer, PropertyStack


class PropertyStackTest(TestCase):
    def testLayer(self):
        om = PropertyStack()
        pm = PropertyLayer()
        pm["testkey"] = "testvalue"
        om.addLayer(1, pm)
        self.assertEqual(om["testkey"], "testvalue")

    def testHighPriority(self):
        om = PropertyStack()
        low_pm = PropertyLayer()
        high_pm = PropertyLayer()
        low_pm["testkey"] = "low value"
        high_pm["testkey"] = "high value"
        om.addLayer(1, low_pm)
        om.addLayer(0, high_pm)
        self.assertEqual(om["testkey"], "high value")

    def testPriorityFallback(self):
        om = PropertyStack()
        low_pm = PropertyLayer()
        high_pm = PropertyLayer()
        low_pm["testkey"] = "low value"
        om.addLayer(1, low_pm)
        om.addLayer(0, high_pm)
        self.assertEqual(om["testkey"], "low value")

    def testLayerRemoval(self):
        om = PropertyStack()
        low_pm = PropertyLayer()
        high_pm = PropertyLayer()
        low_pm["testkey"] = "low value"
        high_pm["testkey"] = "high value"
        om.addLayer(1, low_pm)
        om.addLayer(0, high_pm)
        self.assertEqual(om["testkey"], "high value")
        om.removeLayer(high_pm)
        self.assertEqual(om["testkey"], "low value")

    def testPropertyChange(self):
        layer = PropertyLayer()
        stack = PropertyStack()
        stack.addLayer(0, layer)
        mock = Mock()
        stack.wire(mock.method)
        layer["testkey"] = "testvalue"
        mock.method.assert_called_once_with("testkey", "testvalue")

    def testPropertyChangeEventPriority(self):
        low_layer = PropertyLayer()
        high_layer = PropertyLayer()
        low_layer["testkey"] = "initial low value"
        high_layer["testkey"] = "initial high value"
        stack = PropertyStack()
        stack.addLayer(1, low_layer)
        stack.addLayer(0, high_layer)
        mock = Mock()
        stack.wire(mock.method)
        low_layer["testkey"] = "modified low value"
        mock.method.assert_not_called()
        high_layer["testkey"] = "modified high value"
        mock.method.assert_called_once_with("testkey", "modified high value")
