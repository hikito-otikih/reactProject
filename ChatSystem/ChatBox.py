import sys
import os
from util.Response import (
    Bot_ask_destination, Response, BotResponse, UserResponse, CompositeResponse,
    Bot_ask_clarify, Bot_ask_start_location, Bot_ask_category,
    Bot_suggest_categories, Bot_confirm_start_location, Bot_confirm_destination,
    Bot_suggest_attractions_search, Bot_display_attraction_details, Bot_create_itinerary, Bot_ask_extra_info
)

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.UserInputProcessing import process_user_input

class ChatBox :
    def __init__(self) :
        self.response_history = []
        self.message_history = []  # for process_user_input
        self.collected_information = {
            'start_location' : None,
            'categories': None,
            'destinations': None,
            'budget': None,
            'duration_days': None
        }

    def _add_response(self, response: Response) :
        self.response_history.append(response)
        self.message_history.append({
            'role': response.whom,
            'message': response.get_message()
        })
  
    def _clear_conversation(self) :
        self.response_history = []
        self.message_history = []

    def _computeResponse_from_user_input(self, outputDict: dict) -> BotResponse:
        """
        Process user input and return appropriate BotResponse.
        Uses the full pipeline and converts to concrete Response objects.
        """
        
        function_name = outputDict.get('function')
        params = outputDict.get('params', {})
        text = outputDict.get('text')
        
        # Map function to appropriate Response class
        if function_name == 'ask_clarify':
            return Bot_ask_clarify(text or 'Could you provide more details?')
        
        elif function_name == 'confirm_start_location':
            # user already provided start location
            # ask to fill in missing info...
            # check the outputDict to see what is missing
            if not self.collected_information.get('categories'):
                return Bot_ask_category()
            elif not self.collected_information.get('destinations'):
                return Bot_ask_destination()
        
        elif function_name == 'confirm_destination':
            # user already provided destination
            # ask to fill in missing info or display details...
            if not self.collected_information.get('start_location'):
                return Bot_ask_start_location()
            else:
                return CompositeResponse([Bot_display_attraction_details(), Bot_ask_extra_info()]) # ask for budget/duration/preferences
        
        elif function_name == 'suggest_categories':
            return Bot_suggest_categories()
        
        elif function_name == 'suggest_attractions':
            category = params.get('category', 'attraction')
            location = params.get('location', 'your area')
            limit = params.get('limit', 5)
            return Bot_suggest_attractions_search(category, location, limit)
        
        elif function_name == 'get_attraction_details':
            attraction_name = params.get('attraction_name') or f"Attraction #{params.get('attraction_id')}"
            return Bot_display_attraction_details(attraction_name)
        
        elif function_name == 'itinerary_planning':
            start_location = params.get('start_location')
            categories = params.get('categories', [])
            destinations = params.get('destinations', [])
            duration_days = params.get('duration_days', 1)
            return Bot_create_itinerary(start_location, categories, destinations, duration_days)
        
        else:
            # Default fallback
            return Bot_ask_clarify('I\'m processing your request. Could you provide more details?')
        


    
    def _update_collected_information(self, result: dict) -> None :
        """
        Extract and update collected_information from user input.
        Merges newly extracted slots into the persistent collected_information dict.
        """
        # Get the raw extraction result

        
        # Extract slots from the result
        params = result.get('params', {})
        
        # Update collected_information with new data (only non-null values)
        if params.get('start_location'):
            self.collected_information['start_location'] = params['start_location']
        
        if params.get('categories'):
            self.collected_information['categories'] = params['categories']
        elif params.get('category'):
            # Handle single category
            if self.collected_information['categories']:
                if params['category'] not in self.collected_information['categories']:
                    self.collected_information['categories'].append(params['category'])
            else:
                self.collected_information['categories'] = [params['category']]
        
        if params.get('destinations') or params.get('destination'):
            dest = params.get('destinations') or params.get('destination')
            if isinstance(dest, list):
                self.collected_information['destinations'] = dest
            else:
                self.collected_information['destinations'] = [dest] if dest else None
        
        if params.get('budget'):
            self.collected_information['budget'] = params['budget']
        
        if params.get('duration_days'):
            self.collected_information['duration_days'] = params['duration_days']
        
        # Print for debugging (can be removed later)
        print(f"\n📊 Updated collected_information: {self.collected_information}\n")


    def process_input(self, user_input: str) -> None :
        user_response = UserResponse(user_input)
        self._add_response(user_response)

        outputDict = process_user_input(user_input, self.collected_information, self.message_history)
        
        bot_response = self._computeResponse_from_user_input(outputDict)
        self._add_response(bot_response)
        bot_response.process()

        self._update_collected_information(outputDict)

        return bot_response 

if __name__ == "__main__" :
    # interactive test
    chat_box = ChatBox()
    while True :
        user_input = input("You: ")
        bot_response = chat_box.process_input(user_input)
        print(f"Bot: {bot_response.get_message()}")
