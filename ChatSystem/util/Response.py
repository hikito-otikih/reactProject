import sys
import os
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import random


class Response : 
    def __init__(self,message,whom) : 
        self.message = message
        self.whom = whom
    
    def get_message(self) : 
        return self.message
    
class UserResponse(Response) :
    def __init__(self,user_message,whom='user') : 
        super().__init__(user_message,whom)
    
class BotResponse(Response) :
    def __init__(self,location_sequence, bot_message, suggestions=None, whom='bot') : 
        # if history and history[history.__len__()-1][0]['role'] != 'user':
            # raise ValueError("Last history entry must be 'user'")
        super().__init__(bot_message, whom)
        self.location_sequence = location_sequence
        self.suggestions = suggestions if suggestions is not None else []

    def process(self):
        pass
    
    def get_suggestions(self):
        """Return the list of suggestions for this response"""
        return self.suggestions

    def get_database_results(self) :
        return {
            "No database results for this response type" : []
        }
    
    def get_json_serializable(self):
        return {
            "message" : self.get_message(),
            "suggestions" : self.get_suggestions(),
            "database_results" : self.get_database_results()
        }
class Bot_ask_extra_info(BotResponse) :
    list_of_responses = [
        "Could you provide more details about your budget, duration, number of attractions, or preferences?",
        "To help you better, can you share more about your budget, trip length, limit number of attractions, or interests?",
        "Please tell me more about your budget, how long you'll be traveling, number of attractions, or what you like.",
        "Can you give me additional info on your budget, duration, number of attractions, or travel preferences?",
        "I'd love to assist you better! Could you share more about your budget, trip duration, number of attractions, or interests?"
    ]
    
    static_suggestions = [
        "3 days, budget friendly, 5 attractions",
        "1 week, moderate budget, 10 attractions",
        "Weekend trip, flexible budget, 7 attractions"
    ]
    
    def __init__(self, info_text=None, location_sequence=None) :
        if info_text is None:
            info_text = random.choice(self.list_of_responses)
        super().__init__(location_sequence, info_text, suggestions=self.static_suggestions)
    

class CompositeResponse(BotResponse) :
    def __init__(self, responses, location_sequence=None) :
        combined_message = "\n".join([resp.get_message() for resp in responses])
        # Use suggestions from the last response in the composite
        suggestions = responses[-1].get_suggestions() if responses else []
        super().__init__(location_sequence, combined_message, suggestions=suggestions)
        self.responses = responses
    
    def get_database_results(self):
        """Aggregate database results from all composite responses"""
        results = {}
        for resp in self.responses:
            resp_results = resp.get_database_results()
            for key, value in resp_results.items():
                if key in results:
                    # Merge lists if both are lists
                    if isinstance(results[key], list) and isinstance(value, list):
                        results[key].extend(value)
                    else:
                        results[key] = value
                else:
                    results[key] = value
        return results
     
class Bot_ask_start_location(BotResponse) :
    list_of_responses = [
        "Where do you start your journey from?",
        "Where is your starting point?",
        "Where does the fun begin today?",
        "Let's go, but where first?",
        "Let's have a trip, tell me where to begin!"
    ]
    
    static_suggestions = [
        "Ho Chi Minh City",
        "Hanoi",
        "Da Nang"
    ]

    def __init__(self, location_sequence=None) : 
        super().__init__(location_sequence, random.choice(self.list_of_responses), suggestions=self.static_suggestions)

class Bot_ask_destination(BotResponse) :
    list_of_responses = [
        "What's your destination?",
        "Where would you like to go?",
        "Tell me your target location.",
        "Where are we headed?",
        "What's the place you want to visit?"
    ]
    
    default_suggestions = [
        "Ben Thanh Market",
        "War Remnants Museum",
        "Notre Dame Cathedral"
    ]
    
    def __init__(self, location_sequence) :
        # Generate dynamic suggestions based on start_location
        suggestions = self.default_suggestions
        
        if location_sequence:
            # Get nearby popular attractions from database
            nearby_ids = location_sequence.suggest_for_position()
            if nearby_ids:
                # Convert IDs to names
                suggestions = [location_sequence.id_to_name(pid) for pid in nearby_ids]
                # Filter out None values and ensure we have suggestions
                suggestions = [s for s in suggestions if s] or self.default_suggestions
        
        super().__init__(location_sequence, random.choice(self.list_of_responses), suggestions=suggestions)
        self.nearby_ids = nearby_ids if location_sequence else []
    
    def get_database_results(self):
        """Return nearby destination IDs suggested to user"""
        return {
            'nearby_destination_ids': self.nearby_ids
        }

class Bot_ask_category(BotResponse) :
    list_of_responses = [
        "What type of place are you interested in?",
        "What category of location would you like to explore?",
        "Any specific type of place you have in mind?",
        "What kind of spot are you looking for?",
        "What category of destination are you thinking about?"
    ]
    
    static_suggestions = [
        "Museums & Culture",
        "Parks & Nature",
        "Restaurants & Cafes"
    ]
    
    def __init__(self, location_sequence=None) : 
        super().__init__(location_sequence, random.choice(self.list_of_responses), suggestions=self.static_suggestions)

class Bot_suggest_attraction(BotResponse) :
    list_of_responses = [
        "Based on your preferences, I suggest visiting {location}. It's a great choice!",
        "How about checking out {location}? It fits your interests well.",
        "You might enjoy {location}. It's known for its {category} attractions.",
        "Consider adding {location} to your itinerary. It's perfect for {category} lovers!",
        "{location} is a fantastic spot that aligns with your interests in {category}."
    ]
    
    static_suggestions = [
        "Yes, add it",
        "Show me alternatives",
        "Tell me more about this place"
    ]

    def __init__(self, location, category, location_sequence=None) : 
        response = random.choice(self.list_of_responses).format(location=location, category=category)
        super().__init__(location_sequence, response, suggestions=self.static_suggestions)
        self.db_location = location_sequence.search_by_name(location) if location_sequence else []
    
    def get_database_results(self):
        """Return the suggested attraction IDs"""
        return {
            'suggested_attraction_ids': self.db_location
        }


class Bot_suggest_categories(BotResponse) :
    list_of_responses = [
        "Here are some popular categories: museum, park, restaurant, historical site, shopping area. Which one interests you?",
        "You can choose from categories like museum, park, restaurant, historical site, or shopping area. Any preferences?",
        "Consider these categories: museum, park, restaurant, historical site, shopping area. Do any catch your eye?",
        "Some great categories to explore are museum, park, restaurant, historical site, and shopping area. What do you think?",
        "How about selecting from museum, park, restaurant, historical site, or shopping area? Any favorites?"
    ]
    
    static_suggestions = [
        "museum",
        "park",
        "restaurant"
    ]
    
    def __init__(self, location_sequence=None) : 
        super().__init__(location_sequence, random.choice(self.list_of_responses), suggestions=self.static_suggestions)
        self.suggested_category = location_sequence.get_suggest_category() if location_sequence else []
    
    def get_database_results(self):
        """Return suggested categories"""
        return {
            'suggested_categories': self.suggested_category if isinstance(self.suggested_category, list) else [self.suggested_category]
        }

class Bot_ask_clarify(BotResponse) :
    def __init__(self, clarify_text, suggestions=None, location_sequence=None) : 
        # For clarifications, suggestions should be provided dynamically or use defaults
        if suggestions is None:
            suggestions = [
                "Tell me more",
                "Skip this",
                "Start over"
            ]
        super().__init__(location_sequence, clarify_text, suggestions=suggestions)
    
    def get_database_results(self):
        """No database results for this response type"""
        return {}

class Bot_display_attraction_details(BotResponse) :
    # attributes: id of place in database
    static_suggestions = [
        "Add to itinerary",
        "Show similar places",
        "Tell me more"
    ]
    
    def __init__(self, attraction_name, location_sequence=None) : 
        response = f"Here are the details for {attraction_name}"
        # Frontend can format better 
        # @Huynh Chi Ton
        super().__init__(location_sequence, response, suggestions=self.static_suggestions)
        self.db_attraction = location_sequence.search_by_name(attraction_name) if location_sequence else []
    
    def get_database_results(self):
        """Return the attraction details IDs"""
        return {
            'attraction_detail_id': self.db_attraction
        }

class Bot_suggest_attractions(BotResponse):
    list_of_responses = [
        "I found {limit} great {category} options near {location}. Would you like to see them?",
        "Here are {limit} {category} recommendations in {location} area.",
        "I've got {limit} {category} suggestions around {location} for you!",
        "Let me show you {limit} {category} places near {location}.",
        "Found {limit} amazing {category} spots in {location}!"
    ]
    
    static_suggestions = [
        "Show me details",
        "Find more options",
        "Create itinerary with these"
    ]
    
    def __init__(self, category, location, limit=5, location_sequence=None):
        response = random.choice(self.list_of_responses).format(
            category=category,
            location=location,
            limit=limit
        )
        super().__init__(location_sequence, response, suggestions=self.static_suggestions)
        self.category = category
        self.location = location
        self.limit = limit

        self.suggested_attractions = location_sequence.suggest_for_position(category=category, limit=limit) if location_sequence else []
    
    def get_database_results(self):
        """Return suggested attractions by category"""
        return {
            'suggested_attraction_ids': self.suggested_attractions,
            'category': self.category,
            'location': self.location,
            'limit': self.limit
        }

class Bot_create_itinerary(BotResponse):
    list_of_responses = [
        "Creating a {days}-day itinerary starting from {start}! This will be exciting!",
        "Planning your {days}-day journey from {start}. Give me a moment!",
        "Perfect! I'll design a {days}-day trip beginning at {start}.",
        "Let me craft a {days}-day adventure starting from {start} for you!",
        "Working on your {days}-day itinerary from {start}. Almost ready!"
    ]
    
    static_suggestions = [
        "Looks great!",
        "Modify itinerary",
        "Add more attractions"
    ]

    def __init__(self, history, start_location, categories, destinations, duration_days, location_sequence, limit):
        response = random.choice(self.list_of_responses).format(
            start = start_location or 'your location',
            days = duration_days
        )
        super().__init__(location_sequence, response, suggestions=self.static_suggestions)
        self.start_location = start_location
        self.categories = categories
        self.destinations = destinations
        self.duration_days = duration_days

        self.listOfItinerary = location_sequence.suggest_itinerary_to_sequence(limit) if location_sequence else []
    
    def get_database_results(self):
        """Return the complete itinerary"""
        return {
            'itinerary_ids': self.listOfItinerary,
            'start_location': self.start_location,
            'categories': self.categories,
            'destinations': self.destinations,
            'duration_days': self.duration_days
        }



if __name__ == "__main__":
    botresp = Bot_suggest_attraction("Khách sạn Nikko Saigon","cafe")
    # [[] , [] , []]
    print(type(botresp.id_location))
    for location in botresp.id_location :
        print(location)

    print(botresp.get_message())

