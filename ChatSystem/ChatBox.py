import json
import sys
import os
from urllib import response
from ChatSystem.util.Response import (
    Response, BotResponse, UserResponse, CompositeResponse,
    Bot_ask_clarify, Bot_ask_category,
    Bot_suggest_categories,
    Bot_suggest_attractions, Bot_search_by_name, Bot_create_itinerary, Bot_ask_extra_info,
)

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ChatSystem.util.UserInputProcessing import process_user_input

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
        self.start_conversation()

    def start_conversation(self) -> BotResponse:
        """Proactively initiate the conversation by asking the first question."""
        if not self.conversation_started:
            self.conversation_started = True
            # Start by asking for categories
            bot_response = Bot_suggest_categories(
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
        
        # Map function to appropriate Response class
        if function_name == 'ask_clarify':
            return Bot_ask_clarify(
                text,
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )
    

        elif function_name == 'suggest_categories':
            return Bot_suggest_categories(
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )
        
        elif function_name == 'suggest_attractions':
            # Handle both single category and list of categories
            category = params.get('category')
            if not category:
                categories = params.get('categories', [])
                category = categories[0] if categories else 'attractions'
            
            location = params.get('location') or 'nearby'
            limit = params.get('limit') or params.get('limit_attractions') or self.collected_information.get('limit', 5)
            
            return Bot_suggest_attractions(
                category, location, limit,
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )
        
        elif function_name == 'search_by_name':
            attraction_name = params.get('attraction_name') or params.get('destination') or params.get('name') or 'unknown place'
            return Bot_search_by_name(
                attraction_name,
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )
        
        elif function_name == 'itinerary_planning':
            # Use collected_information as fallback
            categories = params.get('categories') or self.collected_information.get('categories')
            if (not categories) or (isinstance(categories, list) and len(categories) == 0):
                categories = None  # Make it explicit None if empty
            limit = params.get('limit') or self.collected_information.get('limit', 3)
            
            # Categories are now optional - Bot_create_itinerary will handle None/empty categories
            return Bot_create_itinerary(
                categories=categories,  # Can be None or []
                location_sequence=self.location_sequence,
                limit=limit,
                collected_information=self.collected_information
            )
        
        else:
            # Default fallback for unknown functions
            return Bot_ask_clarify(
                text or 'I\'m not sure how to help with that. Could you provide more details?',
                location_sequence=self.location_sequence,
                collected_information=self.collected_information
            )        
    
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
        
        # Update destination (single string value) - kept for Bot_display_attraction_details
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
        
        # Ignore budget, duration_days, dates as they are no longer tracked
        
        # Print for debugging (can be removed later)
        print(f"\n📊 Updated collected_information: {self.collected_information}\n")

    def process_input(self, user_input: str):
        user_response = UserResponse(user_input)
        self._add_response(user_response)

        outputDict = process_user_input(user_input, self.collected_information, self.message_history)
        print("concak0")
        bot_response = self._computeResponse_from_outputDict(outputDict)
        print("concak1")
        self._add_response(bot_response)
        self._update_collected_information(outputDict)
        
        print(f"\n🤖 Bot Response complete\n")
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
                    location_sequence=self.location_sequence,
                    bot_message=response_dict['message'],
                    collected_information=self.collected_information
                )
                # Manually set suggestions if they exist in saved data
                if response_dict.get('suggestions'):
                    response.suggestions = response_dict['suggestions']
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
            for  x in bot_response.get_database_results() :
                print(f"  - {x} {LocationSequence().id_to_name(x)}")
        else:   
            print(f"(No database results.)")

        if bot_response.get_suggestions():
            print(f"💡 Suggestions: {bot_response.get_suggestions()}")

        save_data = chat_box.save_chatbox()
        # print (json.dumps(save_data, indent=2))  # For debugging purposes

        ChatBox.load_chatbox(chat_box, save_data)  # Test loading functionality

        # if save_data.get('responses'):
            # print(f"(Conversation saved with {len(save_data['responses'])} messages.)")
