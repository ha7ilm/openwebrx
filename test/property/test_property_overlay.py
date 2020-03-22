from unittest import TestCase
from unittest.mock import Mock
from owrx.property import PropertyManager, PropertyLayers


class TestPropertyMock(TestCase):
    def testLayer(self):
        om = PropertyLayers()
        pm = PropertyManager()
        pm["testkey"] = "testvalue"
        om.addLayer(1, pm)
        self.assertEqual(om["testkey"], "testvalue")

    def testHighPriority(self):
        om = PropertyLayers()
        low_pm = PropertyManager()
        high_pm = PropertyManager()
        low_pm["testkey"] = "low value"
        high_pm["testkey"] = "high value"
        om.addLayer(1, low_pm)
        om.addLayer(0, high_pm)
        self.assertEqual(om["testkey"], "high value")

    def testPriorityFallback(self):
        om = PropertyLayers()
        low_pm = PropertyManager()
        high_pm = PropertyManager()
        low_pm["testkey"] = "low value"
        om.addLayer(1, low_pm)
        om.addLayer(0, high_pm)
        self.assertEqual(om["testkey"], "low value")

    def testLayerRemoval(self):
        om = PropertyLayers()
        low_pm = PropertyManager()
        high_pm = PropertyManager()
        low_pm["testkey"] = "low value"
        high_pm["testkey"] = "high value"
        om.addLayer(1, low_pm)
        om.addLayer(0, high_pm)
        self.assertEqual(om["testkey"], "high value")
        om.removeLayer(high_pm)
        self.assertEqual(om["testkey"], "low value")
