from unittest import TestCase
from unittest.mock import Mock
from owrx.property import PropertyLayer, PropertyFilter, PropertyDeleted


class PropertyFilterTest(TestCase):
    def testPassesProperty(self):
        pm = PropertyLayer()
        pm["testkey"] = "testvalue"
        mock = Mock()
        mock.apply.return_value = True
        pf = PropertyFilter(pm, mock)
        self.assertEqual(pf["testkey"], "testvalue")

    def testMissesProperty(self):
        pm = PropertyLayer()
        pm["testkey"] = "testvalue"
        mock = Mock()
        mock.apply.return_value = False
        pf = PropertyFilter(pm, mock)
        self.assertFalse("testkey" in pf)
        with self.assertRaises(KeyError):
            x = pf["testkey"]

    def testForwardsEvent(self):
        pm = PropertyLayer()
        mock = Mock()
        mock.apply.return_value = True
        pf = PropertyFilter(pm, mock)
        mock = Mock()
        pf.wire(mock.method)
        pm["testkey"] = "testvalue"
        mock.method.assert_called_once_with({"testkey": "testvalue"})

    def testForwardsPropertyEvent(self):
        pm = PropertyLayer()
        mock = Mock()
        mock.apply.return_value = True
        pf = PropertyFilter(pm, mock)
        mock = Mock()
        pf.wireProperty("testkey", mock.method)
        pm["testkey"] = "testvalue"
        mock.method.assert_called_once_with("testvalue")

    def testForwardsWrite(self):
        pm = PropertyLayer()
        mock = Mock()
        mock.apply.return_value = True
        pf = PropertyFilter(pm, mock)
        pf["testkey"] = "testvalue"
        self.assertTrue("testkey" in pm)
        self.assertEqual(pm["testkey"], "testvalue")

    def testOverwrite(self):
        pm = PropertyLayer()
        pm["testkey"] = "old value"
        mock = Mock()
        mock.apply.return_value = True
        pf = PropertyFilter(pm, mock)
        pf["testkey"] = "new value"
        self.assertEqual(pm["testkey"], "new value")
        self.assertEqual(pf["testkey"], "new value")

    def testRejectsWrite(self):
        pm = PropertyLayer()
        pm["testkey"] = "old value"
        mock = Mock()
        mock.apply.return_value = False
        pf = PropertyFilter(pm, mock)
        with self.assertRaises(KeyError):
            pf["testkey"] = "new value"
        self.assertEqual(pm["testkey"], "old value")

    def testPropagatesDeletion(self):
        pm = PropertyLayer(testkey="somevalue")
        filter_mock = Mock()
        filter_mock.apply.return_value = True
        pf = PropertyFilter(pm, filter_mock)
        mock = Mock()
        pf.wire(mock.method)
        del pf["testkey"]
        mock.method.assert_called_once_with({"testkey": PropertyDeleted})
