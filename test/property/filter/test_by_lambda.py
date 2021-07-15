from owrx.property.filter import ByLambda
from unittest import TestCase
from unittest.mock import Mock


class TestByLambda(TestCase):
    def testPositive(self):
        mock = Mock(return_value=True)
        filter = ByLambda(mock)
        self.assertTrue(filter.apply("test_key"))
        mock.assert_called_with("test_key")

    def testNegateive(self):
        mock = Mock(return_value=False)
        filter = ByLambda(mock)
        self.assertFalse(filter.apply("test_key"))
        mock.assert_called_with("test_key")
