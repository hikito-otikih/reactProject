"""
End-to-end pipeline: User Input → Function Call
Combines orchestrator, translator, and formatter for complete processing.
"""

import json
from typing import Dict
from .orchestrator import extract_info_with_orchestrator
from .translator import translate, detectLanguage
from .Response import (
    Bot_ask_destination, Response, BotResponse, UserResponse, CompositeResponse,
    Bot_ask_clarify, Bot_ask_start_location, Bot_ask_category,
    Bot_suggest_categories,
    Bot_suggest_attractions, Bot_display_attraction_details, Bot_create_itinerary
)

def process_user_input(user_input: str, collected_information: list = None, conversation_history: list = None) -> dict:
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
    extracted_data = extract_info_with_orchestrator(english_input, collected_information, conversation_history)
    
    # Step 3: Format to clean structure
    result = _format_llm_response(extracted_data)
    
    # Translate all text fields back to source language if needed
    if source_language and source_language != 'en' and 'params' in result:
        _translate_all_text_back(result['params'], source_language)
    
    return result


def _format_llm_response(extracted_data: Dict) -> Dict:
    """
    Convert LLM extraction to clean, readable format.
    
    Input: Raw LLM extraction from orchestrator
    Output: Simplified structure for your team
    
    Example:
        Input: {'intents': [{'intent': 'suggest_itinerary', 'slots': {...}}], ...}
        Output: {'action': 'suggest_itinerary', 'params': {...}, 'needs_clarification': False}
    """
    
    # Handle clarification needed
    if extracted_data.get('followup') and extracted_data.get('clarify_question'):
        return {
            'function': 'ask_clarify',
            'text': extracted_data.get('clarify_question'),
        }
    
    # Handle empty/invalid response
    intents = extracted_data.get('intents', [])
    if not intents:
        return {
            'function': 'ask_clarify',
            'text': 'Could you please provide more details?',
            'error': 'No intent detected'
        }
    
    # Extract main intent
    primary = intents[0]
    
    return {
        'function': primary.get('suggested_function') or primary.get('intent'),
        'params': primary.get('slots', {}),
    }


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


