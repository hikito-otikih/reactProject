import json
import sys
import os
from urllib import response
from util.Response import (
    Bot_ask_destination, Response, BotResponse, UserResponse, CompositeResponse,
    Bot_ask_clarify, Bot_ask_start_location, Bot_ask_category,
    Bot_suggest_categories,
    Bot_suggest_attractions, Bot_display_attraction_details, Bot_create_itinerary, Bot_ask_extra_info,
    Bot_suggest_from_database
)

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.UserInputProcessing import process_user_input

from ChatSystem.location_sequence import LocationSequence

class ChatBox :
    def __init__(self,location_sequence: LocationSequence) :
        self.location_sequence = location_sequence
        self.response_history = []
        self.message_history = []  # for process_user_input
        self.collected_information = {
            'destination': None,
            'categories': None,
            'limit': 3
        }
        self.conversation_started = False

    def start_conversation(self) -> BotResponse:
        """Proactively initiate the conversation by asking the first question."""
        if not self.conversation_started:
            self.conversation_started = True
            # Start by asking for the destination
            bot_response = Bot_ask_destination(
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )
            self._add_response(bot_response)
            return bot_response
        return None
    def get_history(self) :
        return self.message_history
    def _add_response(self, response: Response) :
        self.response_history.append(response)
        self.message_history.append({
            'role': response.whom,
            'message': response.get_message()
        })
  
    def _clear_conversation(self) :
        self.response_history = []
        self.message_history = []
    
    def _build_context_string(self) -> str:
        """Build a context string from collected information and recent messages."""
        context_parts = []
        
        # Add collected information
        if self.collected_information:
            info_parts = []
            for key, value in self.collected_information.items():
                if value is not None:
                    info_parts.append(f"{key}: {value}")
            if info_parts:
                context_parts.append("Collected info: " + ", ".join(info_parts))
        
        # Add recent conversation (last 3 messages)
        if self.message_history:
            recent = self.message_history[-3:]
            msg_strs = [f"{m['role']}: {m['message']}" for m in recent]
            context_parts.append("Recent conversation: " + " | ".join(msg_strs))
        
        return " // ".join(context_parts) if context_parts else "Starting new conversation"

    def _computeResponse_from_outputDict(self, outputDict: dict) -> BotResponse:
        """
        Process user input and return appropriate BotResponse.
        Uses the full pipeline and converts to concrete Response objects.
        """
        
        function_name = outputDict.get('function')
        params = outputDict.get('params', {})
        text = outputDict.get('text')
        
        response = None
        
        # Map function to appropriate Response class
        if function_name == 'ask_clarify':
            response = Bot_ask_clarify(
                text,
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )
    
        elif function_name == 'suggest_from_database':
            # Database-driven suggestion based on destination and categories
            destination = params.get('destination')
            categories = params.get('categories')
            response = Bot_suggest_from_database(
                destination=destination,
                categories=categories,
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )
    
        elif function_name == 'suggest_categories':
            response = Bot_suggest_categories(
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )
        
        elif function_name == 'suggest_attractions':
            category = params.get('category', 'attraction')
            location = params.get('location', 'your area')
            limit = params.get('limit_attractions', 5)
            response = Bot_suggest_attractions(
                category, location, limit,
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )
        
        elif function_name == 'get_attraction_details':
            attraction_name = params.get('attraction_name') or f"Attraction #{params.get('attraction_id')}"
            response = Bot_display_attraction_details(
                attraction_name,
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )
        
        elif function_name == 'itinerary_planning':
            destination = params.get('destination')
            categories = params.get('categories', [])
            limit = params.get('limit', self.collected_information.get('limit', 3))
            # Note: start_location is now handled by frontend
            response = Bot_create_itinerary(
                self.message_history, None, categories, destination, 1,
                location_sequence=self.location_sequence, limit=limit,
                collected_information=self.collected_information
            )
        
        else:
            # Default fallback
            response = Bot_ask_clarify(
                'I\'m processing your request. Could you provide more details?',
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )
        
        return response        
    
    def _update_collected_information(self, result: dict) -> None :
        """
        Extract and update collected_information from user input.
        Merges newly extracted slots into the persistent collected_information dict.
        Uses 'all_slots' for comprehensive extraction from all intents.
        Note: start_location is now handled by frontend and should be ignored.
        """
        # Extract slots from the result - use all_slots for comprehensive extraction
        
        # print result for debugging
        print(f"\n📝 process_user_input output: {result}\n")
        params = result.get('all_slots', result.get('params', {}))
        
        # Update destination (single string value)
        if params.get('destination'):
            self.collected_information['destination'] = params['destination']
        elif params.get('destinations'):
            # Handle plural form - take first item if it's a list
            dest = params['destinations']
            if isinstance(dest, list) and len(dest) > 0:
                self.collected_information['destination'] = dest[0]
            elif isinstance(dest, str):
                self.collected_information['destination'] = dest
        
        # Handle categories (list of strings)
        if params.get('categories'):
            if isinstance(params['categories'], list):
                self.collected_information['categories'] = params['categories']
            else:
                self.collected_information['categories'] = [params['categories']]
        elif params.get('category'):
            # Handle single category - append to existing list or create new
            if self.collected_information['categories']:
                if params['category'] not in self.collected_information['categories']:
                    self.collected_information['categories'].append(params['category'])
            else:
                self.collected_information['categories'] = [params['category']]
        
        # Update limit (integer, try multiple field names)
        if params.get('limit'):
            self.collected_information['limit'] = params['limit']
        elif params.get('limit_attractions'):
            self.collected_information['limit'] = params['limit_attractions']
        elif params.get('number_of_places'):
            self.collected_information['limit'] = params['number_of_places']
        
        # Explicitly ignore start_location, budget, duration_days, dates
        # These are either handled by frontend or no longer needed
        
        # Print for debugging (can be removed later)
        print(f"\n📊 Updated collected_information: {self.collected_information}\n")


    def process_input(self, user_input: str):
        user_response = UserResponse(user_input)
        self._add_response(user_response)

        outputDict = process_user_input(user_input, self.collected_information, self.message_history)
        
        bot_response = self._computeResponse_from_outputDict(outputDict)
        self._add_response(bot_response)

        self._update_collected_information(outputDict)

        return bot_response 
    

    def save_chatbox(self) -> dict:
        save_data = {
            'responses' : None,
            'collected_information' : self.collected_information
        }

        for response in self.response_history:
            if save_data['responses'] is None :
                save_data['responses'] = []
            
            response_dict = {
                'whom' : response.whom,
                'message' : response.get_message(),
                'suggestions' : response.get_suggestions(),
                'database_results' : response.get_database_results()
            }
            save_data['responses'].append(response_dict)

        return save_data

    def load_chatbox(self, json_data: dict) -> None :
        self._clear_conversation()
        self.collected_information = json_data.get('collected_information', self.collected_information)

        for response_dict in json_data.get('responses', []) :
            if response_dict['whom'] == 'bot' :
                response = BotResponse(
                    message=response_dict['message'],
                    suggestions=response_dict.get('suggestions', []),
                    database_results=response_dict.get('database_results', []),
                    location_sequence=self.location_sequence
                )
            else :
                response = UserResponse(response_dict['message'])
            
            self._add_response(response)

if __name__ == "__main__" :
    # interactive test
    chat_box = ChatBox(location_sequence=LocationSequence())
    
    # Proactively start the conversation
    print("\n" + "="*50)
    print("🤖 Chatbot is starting the conversation...")
    print("="*50 + "\n")
    
    initial_response = chat_box.start_conversation()
    if initial_response:
        print(f"Bot: {initial_response.get_message()}")
        if initial_response.get_suggestions():
            print(f"💡 Suggestions: {initial_response.get_suggestions()}")
        print()
    
    while True :
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Goodbye! 👋")
            break
            
        bot_response = chat_box.process_input(user_input)
        print(f"Bot: {bot_response.get_message()}")

        if (bot_response.get_database_results()):
            print(f"📚 Database Results: {bot_response.get_database_results()}")
        else:   
            print(f"(No database results.)")

        if bot_response.get_suggestions():
            print(f"💡 Suggestions: {bot_response.get_suggestions()}")

        save_data = chat_box.save_chatbox()
        print (json.dumps(save_data, indent=2))  # For debugging purposes
        # if save_data.get('responses'):
            # print(f"(Conversation saved with {len(save_data['responses'])} messages.)")
