from unittest import TestCase
from owrx.property import PropertyDeletion


class PropertyDeletionTest(TestCase):
    def testDeletionEvaluatesToFalse(self):
        deletion = PropertyDeletion()
        self.assertFalse(deletion)
