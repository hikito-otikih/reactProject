
class Response : 
    categories = [ 
        "accommodation", "activity", "catering",
        "commercial", "education", "entertainment",
        "healthcare", "heritage", "leisure",
        "manufacturing", "natural", "parking",
        "pet", "religion", "rental", 
        "service", "sport", "tourism"
    ]    
    def __init__(self , script, whom) :
        self.whom = whom 
        self.script = script 


class Ask_Start_Location(Response) :
    list_of_responses = [
        "Where do you start your journey from?",
        "Where is your starting point?",
        "Where does the fun begin today?",
        "Let's go, but where first",
        "Let's have a trip, tell me the begin"
    ]
    def __init__(self,history,whom='bot') : 
        if history:
            raise ValueError("History must be empty")
        super().__init__(random.choice(self.list_of_responses),whom)

class Ask_Category(Response) :
    list_of_responses = [
        "What type of place are you interested in?",
        "What category of location would you like to explore?",
        "Any specific type of place you have in mind?",
        "What kind of spot are you looking for?",
        "What category of destination are you thinking about?"
    ]
    def __init__(self,history,whom='bot') : 
        if history and history[history.__len__()-1][0]['role'] != 'user':
            raise ValueError("Last history entry must be 'user'")
        super().__init__(random.choice(self.list_of_responses), whom)

# class Suggest_Location(Response) :
#     list_of_responses = [
#         "How about visiting {location}? It has great reviews!",
#         "{location} is a fantastic choice! You might enjoy it.",
#         "Consider checking out {location}. It's quite popular!",
#         "{location} could be a great addition to your trip!",
#         "You might like {location}. It's worth a visit!"
#         "{location} is a must when you're in the area!"
#     ]
#     def __init__(self,history,location,whom='bot') : 
#         if history and history[history.__len__()-1][0]['role'] != 'user':
#             raise ValueError("Last history entry must be 'user'")
#         response = random.choice(self.list_of_responses).format(location=location)
#         super().__init__(response, whom)
"""there is a famous reurant called {location} you can consider visiting it."""
                    """there is a famous a"""
"""  format : 
    1st Where do you start your journey from?
    2nd What type of place are you interested in?
    3rd Suggest a location based on category and start location
    4th complete the trip plan 
"""
class User_Response(Response): 
    def __init__(self,history,user_input,whom='user') : 
        if history and history[history.__len__()-1][0]['role'] != 'bot':
            raise ValueError("Last history entry must be 'bot'")
        super().__init__(user_input, whom)

