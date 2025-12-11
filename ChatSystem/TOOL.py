from location_sequence import LocationSequence
from ChatBox import ChatBox


class TOOL: 
    def __init__(self): 
        self.sequence = LocationSequence() 
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

    def get_suggest_categories(self):
        return self.sequence.get_suggest_categories()

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
        # self.chatbox._clear_conversation()


if __name__ == "__main__": 
    tool = TOOL() 

    # interactive test
    while True :
        user_input = input("You: ")
        bot_response = tool.process_input(user_input)
        
        # print database results if any
        print("\n" + "="*50)
        if hasattr(bot_response, 'db_attraction'):
            print(f"🏛️  DB Attraction IDs: {bot_response.db_attraction}")
            for id in bot_response.db_attraction :
                print(f"   - {tool.id_to_name(id)}")
            

        if hasattr(bot_response, 'suggested_attractions'):
            print(f"🎯 Suggested Attraction IDs: {bot_response.suggested_attractions}")
            if bot_response.suggested_attractions:
                print(f"   Category searched: {bot_response.category if hasattr(bot_response, 'category') else 'N/A'}")
                print(f"   Limit: {bot_response.limit if hasattr(bot_response, 'limit') else 'N/A'}")
                for id in bot_response.suggested_attractions :
                    print(f"   - {tool.id_to_name(id)}")

        if hasattr(bot_response, 'listOfItinerary'):
            print(f"📋 Itinerary IDs: {bot_response.listOfItinerary}")
            for id in bot_response.listOfItinerary :
                print(f"   - {tool.id_to_name(id)}")
                
        print("="*50 + "\n")
        
        print(f"Bot: {bot_response.get_message()}")