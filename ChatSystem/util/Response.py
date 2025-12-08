
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
    def __init__(self,history,bot_message,whom='bot') : 
        if history and history[history.__len__()-1][0]['role'] != 'user':
            raise ValueError("Last history entry must be 'user'")
        super().__init__(bot_message, whom)

class CompositeResponse(BotResponse) :
    def __init__(self, responses) :
        combined_message = "\n".join([resp.get_message() for resp in responses])
        super().__init__(None, combined_message)
        self.responses = responses
     
class Bot_ask_start_location(BotResponse) :
    list_of_responses = [
        "Where do you start your journey from?",
        "Where is your starting point?",
        "Where does the fun begin today?",
        "Let's go, but where first?",
        "Let's have a trip, tell me where to begin!"
    ]

    def __init__(self, history) : 
        super().__init__(history, random.choice(self.list_of_responses))

class Bot_ask_destination(BotResponse) :
    list_of_responses = [
        "What's your destination?",
        "Where would you like to go?",
        "Tell me your target location.",
        "Where are we headed?",
        "What's the place you want to visit?"
    ]
    def __init__(self, history) : 
        super().__init__(history, random.choice(self.list_of_responses))

class Bot_confirm_start_location(BotResponse):
    list_of_responses = [
        "So you're starting from {location}",
        "Confirmed! Starting point: {location}.",
        "Great! We'll begin your journey from {location}.",
        "Perfect! Your starting location is {location}.",
        "Got it! Starting from {location}. Let's plan your trip!"
    ]
    def __init__(self, history, location):
        response = random.choice(self.list_of_responses).format(location=location)
        super().__init__(history, response)
        self.location = location


class Bot_confirm_destination(BotResponse):
    list_of_responses = [
        "You want to visit {destination}, correct?",
        "So {destination} is on your list?",
        "Great choice! {destination} it is!",
        "Confirmed! Adding {destination} to your itinerary.",
        "Perfect! We'll include {destination} in your trip."
    ]
    def __init__(self, history, destination):
        response = random.choice(self.list_of_responses).format(destination=destination)
        super().__init__(history, response)
        self.destination = destination


class Bot_ask_category(BotResponse) :
    list_of_responses = [
        "What type of place are you interested in?",
        "What category of location would you like to explore?",
        "Any specific type of place you have in mind?",
        "What kind of spot are you looking for?",
        "What category of destination are you thinking about?"
    ]
    def __init__(self, history) : 
        super().__init__(history, random.choice(self.list_of_responses))

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
        super().__init__(None,response)

class Bot_suggest_categories(BotResponse) :
    list_of_responses = [
        "Here are some popular categories: museum, park, restaurant, historical site, shopping area. Which one interests you?",
        "You can choose from categories like museum, park, restaurant, historical site, or shopping area. Any preferences?",
        "Consider these categories: museum, park, restaurant, historical site, shopping area. Do any catch your eye?",
        "Some great categories to explore are museum, park, restaurant, historical site, and shopping area. What do you think?",
        "How about selecting from museum, park, restaurant, historical site, or shopping area? Any favorites?"
    ]
    def __init__(self, history) : 
        super().__init__(history, random.choice(self.list_of_responses))

class Bot_ask_clarify(BotResponse) :
    def __init__(self,clarify_text) : 
        super().__init__(None,clarify_text)


class Bot_display_attraction_details(BotResponse) :
    def __init__(self, history, attraction_name) : 
        response = f"Here are the details for {attraction_name}"
        # Frontend can format better 
        # @Huynh Chi Ton
        super().__init__(history, response)




class Bot_suggest_attractions_search(BotResponse):
    list_of_responses = [
        "I found {limit} great {category} options near {location}. Would you like to see them?",
        "Here are {limit} {category} recommendations in {location} area.",
        "I've got {limit} {category} suggestions around {location} for you!",
        "Let me show you {limit} {category} places near {location}.",
        "Found {limit} amazing {category} spots in {location}!"
    ]
    def __init__(self, history, category, location, limit=5):
        response = random.choice(self.list_of_responses).format(
            category=category,
            location=location,
            limit=limit
        )
        super().__init__(history, response)
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
        super().__init__(history, response)
        self.start_location = start_location
        self.categories = categories
        self.destinations = destinations
        self.duration_days = duration_days
    




