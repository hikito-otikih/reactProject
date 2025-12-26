import sys
import os
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import random
from ChatSystem.location_sequence import LocationSequence

class Response : 
    def __init__(self,message,whom) : 
        self.message = message
        self.whom = whom
    
    def get_message(self) : 
        return self.message
    
    def get_suggestions(self) : 
        return []
    
    def get_database_results(self) :
        """Return list of database result IDs"""
        return []
    
    def get_json_serializable(self):
        return {}
    
class UserResponse(Response) :
    def __init__(self,user_message,whom='user') : 
        super().__init__(user_message,whom)
    
class BotResponse(Response) :
    def __init__(self, location_sequence, bot_message, collected_information=None, num_alternatives=2, whom='bot') : 
        # if history and history[history.__len__()-1][0]['role'] != 'user':
            # raise ValueError("Last history entry must be 'user'")
        super().__init__(bot_message, whom)
        self.location_sequence = location_sequence
        self.suggestions = []
        
        # Auto-enhance suggestions if collected_information is provided
        if collected_information is not None:
            self.enhance_suggestions(collected_information, num_alternatives)
    
    def get_suggestions(self):
        """Return the list of suggestions for this response"""
        return self.suggestions

    def get_database_results(self) :
        """Return list of database result IDs"""
        return []
    
    def get_json_serializable(self):
        return {
            "message" : self.get_message(),
            "suggestions" : self.get_suggestions(),
            "database_results" : self.get_database_results()
        }
    
    def _generate_suggestions(self, collected_information, num_suggestions=2):
        """Generate natural, conversational suggestions that users might want to say or select."""
        suggestions = []
        
        # Map missing fields to natural user responses/questions
        field_to_suggestions = {
            'categories': [
                "Show me museums and art galleries",
                "I'm interested in food and restaurants",
                "Parks and outdoor activities",
                "Historical and cultural sites"
            ],
            'limit': [
                "Just 3 places is enough",
                "Show me 5 attractions",
                "I have time for many places"
            ]
        }
        
        # Find missing fields and add corresponding suggestions
        for key, value in collected_information.items():
            if value is None and key in field_to_suggestions:
                suggestions.extend(field_to_suggestions[key][:2])  # Add up to 2 per missing field
        
        # Add general conversation starters if we have space
        general_alternatives = [
            "What's popular around here?",
            "Help me plan my trip",
            "Tell me about top attractions",
            "I need travel recommendations"
        ]
        
        # Combine and limit total suggestions
        all_suggestions = suggestions + general_alternatives
        
        # Select randomly up to num_suggestions
        if len(all_suggestions) > num_suggestions:
            return random.sample(all_suggestions, num_suggestions)
        else:
            return all_suggestions[:num_suggestions]
    
    def enhance_suggestions(self, collected_information, num_alternatives=1):
        """Enhance base suggestions by adding alternative topic-switching suggestions and database-driven suggestions."""
        alternatives = self._generate_suggestions(collected_information, num_alternatives)
        
        # Add database-driven suggestion if we have categories
        if collected_information.get('categories') and self.location_sequence:
            categories = collected_information['categories']
            if not isinstance(categories, list):
                categories = [categories]
            
            alternatives.append(f"Show me other locations in categories: {', '.join(categories)}")
            # Use suggest_for_position to find nearby attractions by category
            for category in categories:
                db_ids = self.location_sequence.suggest_for_position(category=category, limit=1)
                if db_ids:
                    for id in db_ids:
                        place_name = self.location_sequence.id_to_name(id)
                        if place_name:
                            db_suggestion = f"Tell me about {place_name}"
                            if db_suggestion not in self.suggestions:
                                alternatives.append(db_suggestion)


        next_ids = self.location_sequence.suggest_for_position()
        if next_ids:
            for next_id in next_ids:
                place_name = self.location_sequence.id_to_name(next_id)
                if place_name:
                    # find if place_name is in at least one of the existing suggestions
                    if (not any(place_name in s for s in self.suggestions)):
                        # Multiple paraphrased versions for variety
                        suggestion_templates = [
                            f"I noticed {place_name} is really close to where I'm going. What's it like?",
                            f"I'm heading to a spot right near {place_name}. Any info you can share about it?",
                            f"Since I'll be in the area near {place_name}, can you tell me a bit about it?",
                            f"{place_name} is near my destination, tell me about it",
                            f"I'll be near {place_name}. What can you tell me about this place?",
                            f"Looks like {place_name} is on my route. What's worth knowing about it?"
                        ]
                        next_suggestion = random.choice(suggestion_templates)
                        alternatives.append(next_suggestion)
     
        # Combine base suggestions with alternatives, limiting total to avoid overwhelming user
        enhanced = self.suggestions[:3] + alternatives
        random.shuffle(enhanced)
        self.suggestions = enhanced[:5]  # Max 5 suggestions total
        return self

class Bot_ask_extra_info(BotResponse) :
    list_of_responses = [
        "Could you provide more details about your budget, duration, number of attractions, or preferences?",
        "To help you better, can you share more about your budget, trip length, limit number of attractions, or interests?",
        "Please tell me more about your budget, how long you'll be traveling, number of attractions, or what you like.",
        "Can you give me additional info on your budget, duration, number of attractions, or travel preferences?",
        "I'd love to assist you better! Could you share more about your budget, trip duration, number of attractions, or interests?"
    ]
    
    def __init__(self, info_text=None, location_sequence=None, collected_information=None) :
        if info_text is None:
            info_text = random.choice(self.list_of_responses)
        super().__init__(location_sequence, info_text, collected_information=collected_information)
    

class CompositeResponse(BotResponse) :
    def __init__(self, responses, location_sequence=None) :
        combined_message = "\n".join([resp.get_message() for resp in responses])
        super().__init__(location_sequence, combined_message)
        self.responses = responses
        # Use suggestions from the last response in the composite
        if responses:
            self.suggestions = responses[-1].get_suggestions()
    
    def get_database_results(self):
        """Aggregate database results from all composite responses"""
        results = []
        for resp in self.responses:
            resp_results = resp.get_database_results()
            if isinstance(resp_results, list):
                results.extend(resp_results)
            elif resp_results:  # Handle any non-list, non-empty result
                results.append(resp_results)
        return results
     
class Bot_ask_start_location(BotResponse) :
    list_of_responses = [
        "Where do you start your journey from?",
        "Where is your starting point?",
        "Where does the fun begin today?",
        "Let's go, but where first?",
        "Let's have a trip, tell me where to begin!"
    ]

    def __init__(self, location_sequence=None, collected_information=None) : 
        super().__init__(location_sequence, random.choice(self.list_of_responses), suggestions=[], collected_information=collected_information)

class Bot_ask_destination(BotResponse) :
    list_of_responses = [
        "What's your destination?",
        "Where would you like to go?",
        "Tell me your target location.",
        "Where are we headed?",
        "What's the place you want to visit?"
    ]
    
    def __init__(self, location_sequence, collected_information=None) :
        # Generate dynamic suggestions from database
        nearby_ids = []
        
        if location_sequence:
            # Get nearby popular attractions from database
            nearby_ids = location_sequence.suggest_for_position()
        
        super().__init__(location_sequence, random.choice(self.list_of_responses), collected_information=collected_information)
        self.nearby_ids = nearby_ids
        
        # Add destination suggestions after parent init
        if nearby_ids:
            # Convert IDs to names
            destination_suggestions = [location_sequence.id_to_name(pid) for pid in nearby_ids]
            # Filter out None values and prepend to auto-generated suggestions
            destination_suggestions = [s for s in destination_suggestions if s]
            self.suggestions = destination_suggestions + self.suggestions
    
    def get_database_results(self):
        """Return nearby destination IDs suggested to user"""
        return self.nearby_ids if self.nearby_ids else []

class Bot_ask_category(BotResponse) :
    list_of_responses = [
        "What type of place are you interested in?",
        "What category of location would you like to explore?",
        "Any specific type of place you have in mind?",
        "What kind of spot are you looking for?",
        "What category of destination are you thinking about?"
    ]
    
    def __init__(self, location_sequence=None, collected_information=None) : 
        super().__init__(location_sequence, random.choice(self.list_of_responses), suggestions=[], collected_information=collected_information)

class Bot_suggest_attraction(BotResponse) :
    list_of_responses = [
        "Based on your preferences, I suggest visiting {location}. It's a great choice!",
        "How about checking out {location}? It fits your interests well.",
        "You might enjoy {location}. It's known for its {category} attractions.",
        "Consider adding {location} to your itinerary. It's perfect for {category} lovers!",
        "{location} is a fantastic spot that aligns with your interests in {category}."
    ]

    def __init__(self, location, category, location_sequence=None, collected_information=None) : 
        response = random.choice(self.list_of_responses).format(location=location, category=category)
        super().__init__(location_sequence, response, collected_information=collected_information)
        self.db_location = location_sequence.search_by_name(location) if location_sequence else []
    
    def get_database_results(self):
        """Return the suggested attraction IDs"""
        return self.db_location if self.db_location else []


class Bot_suggest_categories(BotResponse) :
    list_of_responses = [
        "Here are some popular categories: museum, park, restaurant, historical site, shopping area. Which one interests you?",
        "You can choose from categories like museum, park, restaurant, historical site, or shopping area. Any preferences?",
        "Consider these categories: museum, park, restaurant, historical site, shopping area. Do any catch your eye?",
        "Some great categories to explore are museum, park, restaurant, historical site, and shopping area. What do you think?",
        "How about selecting from museum, park, restaurant, historical site, or shopping area? Any favorites?"
    ]
    
    def __init__(self, location_sequence=None, collected_information=None) : 
        super().__init__(location_sequence, random.choice(self.list_of_responses), collected_information=collected_information)
        self.suggested_category = location_sequence.get_suggest_category() if location_sequence else []
    
    def get_database_results(self):
        """Return suggested categories"""
        if isinstance(self.suggested_category, list):
            return self.suggested_category
        elif self.suggested_category:
            return [self.suggested_category]
        return []

class Bot_ask_clarify(BotResponse) :
    def __init__(self, clarify_text, location_sequence=None, collected_information=None) : 
        super().__init__(location_sequence, clarify_text, collected_information=collected_information)
    
    def get_database_results(self):
        """No database results for this response type"""
        return []

class Bot_search_by_name(BotResponse) :
    # attributes: id of place in database
    
    def __init__(self, attraction_name, location_sequence=None, collected_information=None) : 
        response = f"Here are the matching records {attraction_name}"
        # Frontend can format better 
        # @Huynh Chi Ton
        super().__init__(location_sequence, response, collected_information=collected_information)
        self.db_attraction = location_sequence.search_by_name(attraction_name) if location_sequence else []
        print(f"searching for attraction by name: {attraction_name}")
    def get_database_results(self):
        """Return the attraction details IDs"""
        return self.db_attraction if self.db_attraction else []

class Bot_suggest_attractions(BotResponse):
    list_of_responses = [
        "I found {limit} great {category} options near {location}.",
        "Here are {limit} {category} recommendations in {location} area.",
        "I've got {limit} {category} suggestions around {location} for you!",
        "Let me show you {limit} {category} places near {location}.",
        "Found {limit} amazing {category} spots in {location}!"
    ]
    
    def __init__(self, category, location, limit=5, location_sequence=None, collected_information=None):
        response = random.choice(self.list_of_responses).format(
            category=category,
            location=location,
            limit=limit
        )
        super().__init__(location_sequence, response, collected_information=collected_information)
        self.category = category
        self.location = location
        self.limit = limit
        print("querying database for suggestions...")
        if (location_sequence):
            print("location sequence found")
        print(f"category: {category}, limit: {limit}")
        self.suggested_attractions = location_sequence.suggest_for_position(category=category, limit=limit) if location_sequence else []
    
    def get_database_results(self):
        """Return suggested attractions by category"""
        return self.suggested_attractions if self.suggested_attractions else []

class Bot_create_itinerary(BotResponse):
    list_of_responses = [
        "Creating your perfect itinerary! This will be exciting!",
        "Planning your journey. Give me a moment!",
        "Perfect! I'll design a great trip for you.",
        "Let me craft an amazing adventure for you!",
        "Working on your personalized itinerary. Almost ready!"
    ]

    def __init__(self, categories, location_sequence, limit, collected_information=None):
        response = random.choice(self.list_of_responses)
        super().__init__(location_sequence, response, collected_information=collected_information)
        self.categories = categories

        self.listOfItinerary = location_sequence.suggest_itinerary_to_sequence(limit) if location_sequence else []
    
    def get_database_results(self):
        """Return the complete itinerary"""
        return self.listOfItinerary if self.listOfItinerary else []

if __name__ == "__main__":
    botresp = Bot_suggest_attraction("Khách sạn Nikko Saigon","cafe")
    # [[] , [] , []]
    print(type(botresp.id_location))
    for location in botresp.id_location :
        print(location)

    print(botresp.get_message())
