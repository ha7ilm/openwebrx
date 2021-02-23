from owrx.property.filter import ByPropertyName
from unittest import TestCase


class ByPropertyNameTest(TestCase):
    def testNameIsInList(self):
        filter = ByPropertyName("test_key")
        self.assertTrue(filter.apply("test_key"))

    def testNameNotInList(self):
        filter = ByPropertyName("test_key")
        self.assertFalse(filter.apply("other_key"))
