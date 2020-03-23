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
