import sys
import os
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import random
from DataCollector import db_utils  


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
    def __init__(self,bot_message,whom='bot') : 
        # if history and history[history.__len__()-1][0]['role'] != 'user':
            # raise ValueError("Last history entry must be 'user'")
        super().__init__(bot_message, whom)

    def process(self):
        pass

class Bot_ask_extra_info(BotResponse) :
    list_of_responses = [
        "Could you provide more details about your budget, duration, or preferences?",
        "To help you better, can you share more about your budget, trip length, or interests?",
        "Please tell me more about your budget, how long you'll be traveling, or what you like.",
        "Can you give me additional info on your budget, duration, or travel preferences?",
        "I'd love to assist you better! Could you share more about your budget, trip duration, or interests?"
    ]
    def __init__(self,info_text) : 
        super().__init__(info_text)
class CompositeResponse(BotResponse) :
    def __init__(self, responses) :
        combined_message = "\n".join([resp.get_message() for resp in responses])
        super().__init__(combined_message)
        self.responses = responses
     
class Bot_ask_start_location(BotResponse) :
    list_of_responses = [
        "Where do you start your journey from?",
        "Where is your starting point?",
        "Where does the fun begin today?",
        "Let's go, but where first?",
        "Let's have a trip, tell me where to begin!"
    ]

    def __init__(self) : 
        super().__init__(random.choice(self.list_of_responses))

class Bot_ask_destination(BotResponse) :
    list_of_responses = [
        "What's your destination?",
        "Where would you like to go?",
        "Tell me your target location.",
        "Where are we headed?",
        "What's the place you want to visit?"
    ]
    def __init__(self) : 
        super().__init__(random.choice(self.list_of_responses))

class Bot_ask_category(BotResponse) :
    list_of_responses = [
        "What type of place are you interested in?",
        "What category of location would you like to explore?",
        "Any specific type of place you have in mind?",
        "What kind of spot are you looking for?",
        "What category of destination are you thinking about?"
    ]
    def __init__(self) : 
        super().__init__(random.choice(self.list_of_responses))

class Bot_suggest_attraction(BotResponse) :
    list_of_responses = [
        "Based on your preferences, I suggest visiting {location}. It's a great choice!",
        "How about checking out {location}? It fits your interests well.",
        "You might enjoy {location}. It's known for its {category} attractions.",
        "Consider adding {location} to your itinerary. It's perfect for {category} lovers!",
        "{location} is a fantastic spot that aligns with your interests in {category}."
    ]

    def __init__(self,location,category) : 
        response = random.choice(self.list_of_responses).format(location=location,category=category)
        super().__init__(response)
        self.id_location = db_utils.search_by_name(location)


class Bot_suggest_categories(BotResponse) :
    list_of_responses = [
        "Here are some popular categories: museum, park, restaurant, historical site, shopping area. Which one interests you?",
        "You can choose from categories like museum, park, restaurant, historical site, or shopping area. Any preferences?",
        "Consider these categories: museum, park, restaurant, historical site, shopping area. Do any catch your eye?",
        "Some great categories to explore are museum, park, restaurant, historical site, and shopping area. What do you think?",
        "How about selecting from museum, park, restaurant, historical site, or shopping area? Any favorites?"
    ]
    def __init__(self) : 
        super().__init__(random.choice(self.list_of_responses))

class Bot_ask_clarify(BotResponse) :
    def __init__(self,clarify_text) : 
        super().__init__(clarify_text)

class Bot_display_attraction_details(BotResponse) :
    # attributes: id of place in database
    def __init__(self, attraction_name) : 
        response = f"Here are the details for {attraction_name}"
        # Frontend can format better 
        # @Huynh Chi Ton
        super().__init__(response)

class Bot_suggest_attractions_search(BotResponse):
    list_of_responses = [
        "I found {limit} great {category} options near {location}. Would you like to see them?",
        "Here are {limit} {category} recommendations in {location} area.",
        "I've got {limit} {category} suggestions around {location} for you!",
        "Let me show you {limit} {category} places near {location}.",
        "Found {limit} amazing {category} spots in {location}!"
    ]
    def __init__(self, category, location, limit=5):
        response = random.choice(self.list_of_responses).format(
            category=category,
            location=location,
            limit=limit
        )
        super().__init__(response)
        self.category = category
        self.location = location
        self.limit = limit

class Bot_create_itinerary(BotResponse):
    list_of_responses = [
        "Creating a {days}-day itinerary starting from {start}! This will be exciting!",
        "Planning your {days}-day journey from {start}. Give me a moment!",
        "Perfect! I'll design a {days}-day trip beginning at {start}.",
        "Let me craft a {days}-day adventure starting from {start} for you!",
        "Working on your {days}-day itinerary from {start}. Almost ready!"
    ]

    def __init__(self, history, start_location, categories, destinations, duration_days):
        response = random.choice(self.list_of_responses).format(
            start = start_location or 'your location',
            days = duration_days
        )
        super().__init__(response)
        self.start_location = start_location
        self.categories = categories
        self.destinations = destinations
        self.duration_days = duration_days




if __name__ == "__main__":
    botresp = Bot_suggest_attraction("Quận 1","cafe")
    print(botresp.id_location)

    print(botresp.get_message())   

