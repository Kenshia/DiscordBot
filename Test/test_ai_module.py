import unittest
import ai_module as ai


class TestAIModule(unittest.TestCase):
    response = ai.response_from_text("Hello, how are you?")

    def test_response_not_none(self):
        self.assertIsNotNone(self.response)
        self.assertNotEqual(self.response, "")

    def test_response_is_string(self):
        self.assertIsInstance(self.response, str)


if __name__ == '__main__':
    unittest.main()
