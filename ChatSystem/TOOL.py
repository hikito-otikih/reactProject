from location_sequence import LocationSequence
from ChatBox import ChatBox


class TOOL: 
    def __init__(self): 
        self.sequence =  LocationSequence() 
        self.chatbox = ChatBox(self.sequence)
    
    def load(self, history) : 
        pass 

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
        response = self.chatbox.process_input(user_input)
        id = response.get
        return self.chatbox.process_input(user_input)
    
    def clear_conversation(self) :
        pass 
        
if __name__ == "__main__":
    tool = TOOL()
    print(tool.search_by_name("three oclock",exact=True,limit=5))
    tool.append(0,1) 
    tool.append(1,2)
    tool.append(2,3)
    # print(tool.get_suggest_category())
    print(tool.suggest_for_position(position=1,limit=3,category=None))
    print(tool.get_suggest_category())
    # print(tool.id_to_name(1)) 
    print(tool.get_sequence())
    print(tool.search_by_name("three oclock",exact=True,limit=5))
    print(tool.suggest_around(lat=10.7721,lon=106.6983,limit=3,category=None))