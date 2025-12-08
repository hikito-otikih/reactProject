"""
End-to-end pipeline: User Input → Function Call
Combines orchestrator, translator, and formatter for complete processing.
"""

import json
from .orchestrator import extract_info_with_orchestrator
from .translator import translate, detectLanguage
from .function_dispatcher import format_llm_response
from .Response import (
    Bot_ask_destination, Response, BotResponse, UserResponse, CompositeResponse,
    Bot_ask_clarify, Bot_ask_start_location, Bot_ask_category,
    Bot_suggest_categories, Bot_confirm_start_location, Bot_confirm_destination,
    Bot_suggest_attractions_search, Bot_display_attraction_details, Bot_create_itinerary
)

def process_user_input(user_input: str, conversation_history: list = None) -> dict:
    """
    End-to-end function: User text → Function name + params
    
    Pipeline:
    1. Detect language and translate to English (if needed)
    2. Extract intent using 2-pass orchestrator
    3. Format to clean function call structure
    
    Parameters:
        user_input (str): User's message in any language
        conversation_history (list): Previous conversation context
            Format: [{'role': 'user'/'bot', 'message': 'text'}, ...]
    
    Returns:
        dict: {
            'function': 'function_name',
            'params': {...},
            'text': 'clarification_text' (only if asking for clarification)
        }
    
    Example:
        >>> process_user_input("Tôi muốn đi tham quan bảo tàng ở quận 1")
        {
            'function': 'suggest_attractions',
            'params': {
                'category': 'museum',
                'location': 'District 1'
            }
        }
    """
    
    if not user_input or not user_input.strip():
        return {
            'function': 'ask_clarify',
            'text': 'Please provide more information about your travel plans.'
        }
    
    # Step 1: Language detection and translation
    source_language = detectLanguage(user_input)
    english_input = translate(user_input, target_language='en') if source_language != 'en' else user_input
    
    # Step 2: Extract intent using 2-pass orchestrator
    extracted_data = extract_info_with_orchestrator(english_input, conversation_history)
    
    # Step 3: Format to clean structure
    result = format_llm_response(extracted_data)
    
    # Translate all text fields back to source language if needed
    if source_language and source_language != 'en' and 'params' in result:
        _translate_all_text_back(result['params'], source_language)
    
    return result


def _translate_all_text_back(params: dict, target_language: str):
    """
    Recursively find and translate all text fields that differ from source language.
    
    Translates any string value in the params dict that's not in the target language.
    Handles nested dicts and lists recursively.
    """
    if not params or not target_language:
        return
    
    for key, value in params.items():
        if isinstance(value, str) and value.strip():
            # Check if text is in different language than target
            detected_lang = detectLanguage(value)
            if detected_lang and detected_lang != target_language:
                params[key] = translate(value, target_language=target_language)
        
        elif isinstance(value, list):
            # Process each item in list
            translated_list = []
            for item in value:
                if isinstance(item, str) and item.strip():
                    detected_lang = detectLanguage(item)
                    if detected_lang and detected_lang != target_language:
                        translated_list.append(translate(item, target_language=target_language))
                    else:
                        translated_list.append(item)
                elif isinstance(item, dict):
                    _translate_all_text_back(item, target_language)
                    translated_list.append(item)
                else:
                    translated_list.append(item)
            params[key] = translated_list
        
        elif isinstance(value, dict):
            # Recursively translate nested dictionaries
            _translate_all_text_back(value, target_language)

def convert_userInput_to_response(user_input: str, conversation_history: list = None) -> Response:
    """
    Convert raw user input to appropriate Response object based on function output.
    
    Parameters:
        user_input (str): Raw input from user.
        conversation_history (list): Conversation context.
    
    Returns:
        Response: BotResponse subclass based on function type.
    """
    outputDict = process_user_input(user_input, conversation_history)
    
    function_name = outputDict.get('function')
    params = outputDict.get('params', {})
    text = outputDict.get('text')
    
    # Map function to appropriate Response class
    if function_name == 'ask_clarify':
        return Bot_ask_clarify(conversation_history, text or 'Could you provide more details?')
    
    elif function_name == 'confirm_start_location':
        location = params.get('location')
        if location:
            return CompositeResponse([Bot_confirm_start_location(conversation_history, location),
                                      Bot_ask_destination(conversation_history)])
        else:
            return Bot_ask_start_location(conversation_history)
    
    elif function_name == 'confirm_destination':
        destination = params.get('destination')
        if destination:
            return CompositeResponse([Bot_confirm_destination(conversation_history, destination),
                                      Bot_ask_category(conversation_history)])
        else:
            return Bot_ask_category(conversation_history)
    
    elif function_name == 'suggest_categories':
        return Bot_suggest_categories(conversation_history)
    
    elif function_name == 'suggest_attractions':
        category = params.get('category', 'attraction')
        location = params.get('location', 'your area')
        limit = params.get('limit', 5)
        return Bot_suggest_attractions_search(conversation_history, category, location, limit)
    
    elif function_name == 'get_attraction_details':
        attraction_name = params.get('attraction_name') or f"Attraction #{params.get('attraction_id')}"
        return Bot_display_attraction_details(conversation_history, attraction_name)
    
    elif function_name == 'itinerary_planning':
        start_location = params.get('start_location')
        categories = params.get('categories', [])
        destinations = params.get('destinations', [])
        duration_days = params.get('duration_days', 1)
        return Bot_create_itinerary(conversation_history, start_location, categories, destinations, duration_days)
    
    else:
        # Default fallback
        return Bot_ask_clarify(conversation_history, 'I\'m processing your request. Could you provide more details?')


if __name__ == "__main__":
    print("=== End-to-End User Input Processing ===\n")
    
    test_cases = [
        {
            'input': "5",
            'history': [
                {'role' : 'user', 'message' : 'I am in District 1, i want to explore the area.'},
                {'role' : 'bot', 'message' : 'Please tell me how many places you would like to visit.'},
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['input']}")
        result = process_user_input(test_case['input'], test_case['history'])
        print("Output:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n" + "="*70 + "\n")


