import os 
from dotenv import load_dotenv
import random  
import json 
from Response import Response
load_dotenv()



GEMINI_KEY= os.getenv('GEMINI_KEY')



class Chatbot :
    def __init__(self):
        self.history = []
    def clear(self) : 
        self.history.clear() 

    def Answer_User_Input(self, user_input) :
        #history = self.history  
        if not self.history : 
            raise ValueError("No chat history available")
        
        last_question = self.history[-1] 
        
        return {} 

    def response(self , user_input) :
        reply = {}
        if not self.history :
            # no chat history yet
            reply ['whom'] = 'bot'
            reply['response'] = Ask_Start_Location(self.history).script
            #reply['suggsetions']  = []
            self.history.append(reply) 
        else : 
            # continue the chat

            user_response = {}  
            user_response['whom'] = 'user' 
            user_response['response'] = user_input 
            reply  =  Answer_User_Input(self, user_input)
            self.history.append(user_response) 
            self.history.append(reply) 
        return json.dumps(reply)


                 

if __name__ == "__main__" : 
    chatbot = Chatbot() 
    print(chatbot.response("ioafoasjfoaisf")) 


"""
    Json Response Format : 
    {
        "whom" : "<bot/user>",
        "response" : "<response_text>",
        "suggestinons" : ["<suggestion1>", "<suggestion2>", ...]
        "command" : {
            "name" : "<command_name>",
            "parameters" : {
                "<param1>" : "<value1>",
                "<param2>" : "<value2>",
                ...
            }
        }
    }
"""
