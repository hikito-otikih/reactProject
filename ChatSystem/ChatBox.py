import sys
import os
from util.Response import Response, BotResponse, UserResponse
# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.UserInputProcessing import process_user_input, convert_userInput_to_response
# class ChatBox:
  # stored attributes and methods:
  #  - conversation_history: 
  #     + list of Response
  #     + list of "role", "message" dict for process_user_input
  #  - add_response(response)
  #  - clear_conversation()


class ChatBox :
    def __init__(self) :
        self.response_history = []
        self.message_history = []  # for process_user_input
    
    def add_response(self, response: Response) :
        self.response_history.append(response)
        self.message_history.append({
            'role': response.whom,
            'message': response.get_message()
        })
  
    def clear_conversation(self) :
        self.response_history = []
        self.message_history = []

    def ComputeResponse_from_user_input(self, user_input: str) -> BotResponse:
        """
        Process user input and return appropriate BotResponse.
        Uses the full pipeline and converts to concrete Response objects.
        """
        return convert_userInput_to_response(user_input, self.message_history)

    def process_input(self, user_input: str) -> None :
        user_response = UserResponse(user_input)
        self.add_response(user_response) ## add to history
        bot_response = self.ComputeResponse_from_user_input(user_input)
        self.add_response(bot_response)
        bot_response.process() ## process the response
        return bot_response 

if __name__ == "__main__" :
    # interactive test
    chat_box = ChatBox()
    while True :
        user_input = input("You: ")
        bot_response = chat_box.process_input(user_input)
        print(f"Bot: {bot_response.get_message()}")
