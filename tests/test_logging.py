import unittest
import logging
from src.ey_analytics.utils.logger import SetUpLogging


class TestLogging(unittest.TestCase):
    def setUp(self):
        self.setUpLogging = SetUpLogging()

    def tearDown(self):
        logging.shutdown()

    def test_function_logger(self):
        @SetUpLogging.function_logger
        def test_function():
            assert 1 == 1
        test_function()

    def test_class_logger(self):
        class TestClass:
            @SetUpLogging.class_logger
            def test_method(self):
                assert 1 == 1
        test = TestClass()
        test.test_method()


if __name__ == '__main__':
    unittest.main()
