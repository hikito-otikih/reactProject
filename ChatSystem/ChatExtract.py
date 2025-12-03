"""
Extract Info Module
Extracts journey planning information from natural language using Gemini API.
"""

import json
import os
import requests
import math
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()


def extract_info(text):
    """
    Extract answer or request from user . 
    Args:
        text : a text string contain user query of answer of a question or request . 
    Returns:
        dict : 
            {
                type : 'answer' or 'request' ,
                if answer : 
                {
                    "must_go_categories":[{"category":"restaurant","order":1,"count":1}],
                    "must_go_destinations":[{"name":"starting point","order":0}],
                    "journey_sequence":[{"type":"destination","value":"starting point","order":0},{"type":"category","value":"airport","order":1}],"number_of_destinations":4,"journey_date":"2025-11-20","start_time":"09:00" 
                }
            } 
    """
    api_key = os.getenv('GEMINI_KEY')
    url = "https://gemini.googleapis.com/v1/models/gemini-1.5-pro:generateText"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    prompt = f"""
You are an expert in extracting structured information from user inputs for journey planning.
Extract the relevant information from the following user input: "{text}"
Respond in JSON format with the following structure:

if __name__ == "__main__":
    pass 