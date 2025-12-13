import sys
import os
from urllib import response
from util.Response import (
    Bot_ask_destination, Response, BotResponse, UserResponse, CompositeResponse,
    Bot_ask_clarify, Bot_ask_start_location, Bot_ask_category,
    Bot_suggest_categories,
    Bot_suggest_attractions, Bot_display_attraction_details, Bot_create_itinerary, Bot_ask_extra_info
)

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.UserInputProcessing import process_user_input
from util.orchestrator import generate_dynamic_suggestions

from ChatSystem.location_sequence import LocationSequence

class ChatBox :
    def __init__(self,location_sequence: LocationSequence) :
        self.location_sequence = location_sequence
        self.response_history = []
        self.message_history = []  # for process_user_input
        self.collected_information = {
            'start_location' : None,
            'categories': None,
            'destinations': None,
            'budget': None,
            'duration_days': None,
            'limit_attractions': 5
        }
        self.conversation_started = False

    def start_conversation(self) -> BotResponse:
        """Proactively initiate the conversation by asking the first question."""
        if not self.conversation_started:
            self.conversation_started = True
            # Start by asking for the start location
            bot_response = Bot_ask_start_location(location_sequence=self.location_sequence)
            # Enhance with alternatives
            bot_response.suggestions = self._enhance_suggestions_with_alternatives(
                bot_response.suggestions, 
                num_alternatives=2
            )
            self._add_response(bot_response)
            bot_response.process()
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
    
    def _generate_alternative_suggestions(self, num_suggestions=2) -> list:
        """Generate alternative questions based on missing information in collected_information."""
        alternatives = []
        
        # Map missing fields to question templates
        field_to_question = {
            'start_location': "Where should I start from?",
            'categories': "What type of places interest me?",
            'destinations': "Which attractions should I visit?",
            'budget': "What's my budget?",
            'duration_days': "How many days do I have?"
        }
        
        # Find missing fields
        missing_fields = []
        for key, value in self.collected_information.items():
            if value is None and key in field_to_question:
                missing_fields.append(field_to_question[key])
        
        # Add some general alternatives
        general_alternatives = [
            "Tell me about popular attractions",
            "Suggest me some categories",
            "What are the best places to visit?",
            "Help me plan a complete trip"
        ]
        
        # Combine missing fields questions with general alternatives
        all_alternatives = missing_fields + general_alternatives
        
        # Select randomly up to num_suggestions
        import random
        if len(all_alternatives) > num_suggestions:
            alternatives = random.sample(all_alternatives, num_suggestions)
        else:
            alternatives = all_alternatives[:num_suggestions]
        
        return alternatives

    def _enhance_suggestions_with_alternatives(self, base_suggestions: list, num_alternatives=1) -> list:
        """Enhance base suggestions by adding alternative topic-switching suggestions."""
        alternatives = self._generate_alternative_suggestions(num_alternatives)
        # Combine base suggestions with alternatives, limiting total to avoid overwhelming user
        enhanced = base_suggestions[:3] + alternatives
        return enhanced[:5]  # Max 5 suggestions total

    def _computeResponse_from_user_input(self, outputDict: dict) -> BotResponse:
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
            # Generate dynamic suggestions for clarification
            context = self._build_context_string()
            suggestions = generate_dynamic_suggestions(
                context=context,
                question=text or 'Could you provide more details?',
                num_suggestions=3
            )
            response = Bot_ask_clarify(
                text or 'Could you provide more details?', 
                suggestions=suggestions,
                location_sequence=self.location_sequence
            )

        elif function_name == 'confirm_start_location':
            # user already provided start location
            # ask to fill in missing info...
            # check the outputDict to see what is missing
            if not self.collected_information.get('categories'):
                response = Bot_ask_category(location_sequence=self.location_sequence)
            elif not self.collected_information.get('destinations'):
                # Pass the start_location to get dynamic suggestions
                response = Bot_ask_destination(
                    location_sequence=self.location_sequence
                )
            else:
                # All info collected, suggest extra details
                response = Bot_ask_extra_info(location_sequence=self.location_sequence)
        
        elif function_name == 'confirm_destination':
            if not self.collected_information.get('start_location'):
                response = Bot_ask_start_location(location_sequence=self.location_sequence)
            else:
                response = CompositeResponse([
                    Bot_display_attraction_details(self.collected_information.get('destinations'), location_sequence=self.location_sequence), 
                    Bot_ask_extra_info(location_sequence=self.location_sequence)
                ], location_sequence=self.location_sequence)
    
        elif function_name == 'suggest_categories':
            response = Bot_suggest_categories(location_sequence=self.location_sequence)
        
        elif function_name == 'suggest_attractions':
            category = params.get('category', 'attraction')
            location = params.get('location', 'your area')
            limit = params.get('limit_attractions', 5)
            response = Bot_suggest_attractions(category, location, limit, location_sequence=self.location_sequence)
        
        elif function_name == 'get_attraction_details':
            attraction_name = params.get('attraction_name') or f"Attraction #{params.get('attraction_id')}"
            response = Bot_display_attraction_details(attraction_name, location_sequence=self.location_sequence)
        
        elif function_name == 'itinerary_planning':
            start_location = params.get('start_location')
            categories = params.get('categories', [])
            destinations = params.get('destinations', [])
            duration_days = params.get('duration_days', 1)
            response = Bot_create_itinerary(self.message_history, start_location, categories, destinations, duration_days, location_sequence=self.location_sequence, limit = self.collected_information.get('limit_attractions',5))
        
        else:
            # Default fallback with dynamic suggestions
            context = self._build_context_string()
            suggestions = generate_dynamic_suggestions(
                context=context,
                question='I\'m processing your request. Could you provide more details?',
                num_suggestions=3
            )
            response = Bot_ask_clarify(
                'I\'m processing your request. Could you provide more details?',
                suggestions=suggestions,
                location_sequence=self.location_sequence
            )

        # Enhance all responses with alternative suggestions
        if response:
            response.suggestions = self._enhance_suggestions_with_alternatives(response.suggestions, 2)
        
        return response        
    
    def _update_collected_information(self, result: dict) -> None :
        """
        Extract and update collected_information from user input.
        Merges newly extracted slots into the persistent collected_information dict.
        Uses 'all_slots' for comprehensive extraction from all intents.
        """
        # Extract slots from the result - use all_slots for comprehensive extraction
        
        # print result for debugging
        print(f"\n📝 process_user_input output: {result}\n")
        params = result.get('all_slots', result.get('params', {}))
        
        # Update collected_information with new data (only non-null values)
        if params.get('start_location'):
            self.collected_information['start_location'] = params['start_location']
        
        # Handle categories (both plural and singular)
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
        
        # Handle destinations (both plural and singular)
        if params.get('destinations'):
            if isinstance(params['destinations'], list):
                self.collected_information['destinations'] = params['destinations']
            else:
                self.collected_information['destinations'] = [params['destinations']]
        elif params.get('destination'):
            dest = params['destination']
            if self.collected_information['destinations']:
                if dest not in self.collected_information['destinations']:
                    self.collected_information['destinations'].append(dest)
            else:
                self.collected_information['destinations'] = [dest]
        
        # Update budget
        if params.get('budget'):
            self.collected_information['budget'] = params['budget']
        
        # Update duration_days (try both field names)
        if params.get('duration_days'):
            self.collected_information['duration_days'] = params['duration_days']
        elif params.get('duration'):
            self.collected_information['duration_days'] = params['duration']
        
        # Update limit_attractions (try multiple field names)
        if params.get('limit_attractions'):
            self.collected_information['limit_attractions'] = params['limit_attractions']
        elif params.get('limit'):
            self.collected_information['limit_attractions'] = params['limit']
        elif params.get('number_of_places'):
            self.collected_information['limit_attractions'] = params['number_of_places']
        
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
            
        bot_response = chat_box.process_input(user_input).get_json_serializable()
        print(bot_response)
        # print(f"Bot: {bot_response.get_message()}")
        # if (bot_response.get_database_results()):
        #     print(f"📚 Database Results: {bot_response.get_database_results()}")
        # if bot_response.get_suggestions():
        #     print(f"💡 Suggestions: {bot_response.get_suggestions()}")