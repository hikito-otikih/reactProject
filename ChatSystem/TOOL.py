import json
import os
from location_sequence import LocationSequence
from ChatBox import ChatBox


class TOOL: 
    def __init__(self): 
        self.sequence =  LocationSequence() 
        self.chatbox = ChatBox(self.sequence)
        
    def load(self, history) : 
        self.chatbox.load_chatbox(history["history"])
        self.sequence.load_sequence(history["start_coordinate"], history["sequence"])
    def save(self) : 
        history = self.chatbox.save_chatbox()
        sequence = self.sequence.get_sequence()  
        return {
            "history" : history,
            "start coordinate" : self.sequence.get_start_coordinate(),
            "sequence" : sequence
        }
    
    # location sequence related
    def append(self , position , ID ) : 
        self.sequence.append(position,ID) 

    def pop(self , position ) : 
        self.sequence.pop(position) 

    def get_sequence(self) : 
        return self.sequence.get_sequence()
    
    def clear_sequence(self): 
        self.sequence.clear_sequence()
    
    def id_to_name(self, placeid) :
        return self.sequence.id_to_name(placeid)
    
    def input_start_coordinate(self, lat: float, lon: float):
        return self.sequence.input_start_coordinate(lat, lon)
    
    def get_start_coordinate(self):
        return self.sequence.get_start_coordinate()
    
    def search_by_name(self,name,exact=False,limit=10):
        return self.sequence.search_by_name(name,exact,limit)

    def get_suggest_category(self):
        return self.sequence.get_suggest_category()

    def suggest_for_position(self, position=-1, category=None, limit=5):
        # Forward with explicit keywords to avoid argument-order mistakes
        return self.sequence.suggest_for_position(pos=position, category=category, limit=limit)
    
    def suggest_around(self, lat, lon, limit=5, category=None):
        # Use keywords to align with LocationSequence signature
        return self.sequence.suggest_around(lat=lat, lon=lon, limit=limit, category=category)

    def suggest_itinerary_to_sequence(self, limit=5):
        return self.sequence.suggest_itinerary_to_sequence(limit)
    
    # chatbox related  
    def process_input(self, user_input : str): 
        if user_input == "" :
            return self.chatbox.start_conversation().get_json_serializable()
        return self.chatbox.process_input(user_input=user_input).get_json_serializable()
    def clear_conversation(self) :
        pass 
if __name__ == "__main__":
    tool = TOOL()
    while True:
        user_input = input("User: ")
        response = tool.process_input(user_input)
        print(json.dumps(response, indent=2)) 
"""
{
  "history": {
    "responses": [
      {
        "whom": "bot",
        "message": "Where does the fun begin today?",
        "suggestions": [
          "What type of places interest me?",
          "Which attractions should I visit?"
        ],
        "database_results": []
      },
      {
        "whom": "user",
        "message": "ho chi minh ",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      }
    ]
  },
  "start_coordinate": [
    10.7628356,
    106.6824824
  ],
  "sequence": [1,2,3]
}
"""