import unittest
from backend.chatbot_engine import ChatbotEngine

class TestChatbot(unittest.TestCase):

    def setUp(self):
        self.chatbot = ChatbotEngine()

    def test_response_to_greeting(self):
        response = self.chatbot.get_response("Hello")
        self.assertIn("Hello", response)

    def test_response_to_farewell(self):
        response = self.chatbot.get_response("Goodbye")
        self.assertIn("Goodbye", response)

    def test_response_to_unknown_input(self):
        response = self.chatbot.get_response("What is your name?")
        self.assertIn("I am a chatbot", response)

if __name__ == "__main__":
    unittest.main()