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

    def clear_sequence(self): 
        self.sequence.clear() 
    
    def id_to_name(self, placeid) :
        return self.sequence.id_to_name(placeid)
    
    def search_by_name(self,name,exact=False,limit=10):
        return self.sequence.search_by_name(name,exact,limit)

    def get_suggest_category(self):
        return self.sequence.get_suggest_category()

    def suggest_for_position(self,position,limit=5,category=None):
        return self.sequence.suggest_for_position(position,limit,category)
    
    def suggest_around(self,lat,lon,limit=5,category=None):
        return self.sequence.suggest_around(lat,lon,limit,category)

    def suggest_itinerary_to_sequence(self, limit=5):
        return self.sequence.suggest_itinerary(limit)

    # chatbox related  
    def process_input(self, user_input : str):
        return self.chatbox.process_input(user_input)
    
    def clear_conversation(self) :
        pass 
    
if __name__ == "__main__":
    tool = TOOL()
    tool.append(0,1) 
    print(tool.get_suggest_category())
    print(tool.id_to_name(1)) 
