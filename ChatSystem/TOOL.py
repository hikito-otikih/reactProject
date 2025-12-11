from ChatSystem.location_sequence import LocationSequence
from ChatSystem.ChatBox import Chatbox


class TOOL: 
    def __init__(self): 
        self.sequence =  LocationSequence() 
        self.chatbox = Chatbox(self.sequence)
    def load(self, history) : 
        pass 

    # location sequence related
    def append(self , position , ID ) : 
        self.sequence.append(position,ID) 

    def pop(self , position ) : 
        self.sequence.remove(position) 
    

    def clear_sequence(self): 
        self.sequence.clear() 
    


    # chatbox related  
    def process_input(self, user_input : str):
        return self.chatbox.process_input(user_input)
    
    def clear_conversation(self) :
        pass 
        # self.chatbox._clear_conversation()
