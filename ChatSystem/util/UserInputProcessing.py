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

def process_user_input(user_input: str, collected_information: dict, conversation_history: list) -> dict:    
    if not user_input or not user_input.strip():
        return {
            'function': 'ask_clarify',
            'text': 'Please provide more information about your travel plans.'
        }
    
    # Step 1: Language detection and translation
    source_language = detectLanguage(user_input)
    english_input = translate(user_input, target_language='en') if source_language != 'en' else user_input
    
    # Translate conversation history to English for context
    english_history = []
    for message in conversation_history:
        msg_text = message.get('message', '')
        if msg_text and detectLanguage(msg_text) != 'en':
            translated_text = translate(msg_text, target_language='en')
            english_history.append({
                'role': message.get('role', ''),
                'message': translated_text
            })
        else:
            english_history.append(message)
            
    # Step 2: Extract intent using 2-pass orchestrator
    extracted_data = extract_info_with_orchestrator(english_input, collected_information, english_history)
    
    # Step 3: Format to clean structure
    # Can be removed with better orchestrator output
    result = _format_llm_response(extracted_data)
    
    # DO NOT translate back - keep everything in English for internal processing
    # Translation should only be done for user-facing messages, not for data structures
    # that will be stored and reused in collected_information
    
    return result


def _format_llm_response(extracted_data: Dict) -> Dict:
    """
    Convert LLM extraction to clean, readable format.
    Returns ALL extracted data regardless of function relevance.
    
    Input: Raw LLM extraction from orchestrator
    Output: Simplified structure with all extracted information
    
    Example:
        Input: {'intents': [{'intent': 'suggest_itinerary', 'slots': {...}}], ...}
        Output: {'function': 'suggest_itinerary', 'params': {...}, 'all_slots': {...}}
    """
    
    # Extract all intents first to preserve information
    intents = extracted_data.get('intents', [])
    
    # Merge ALL slots from ALL intents - do this FIRST
    all_extracted_slots = {}
    primary_slots = {}
    primary_function = None
    
    if intents:
        # Get primary intent info
        primary = intents[0]
        primary_function = primary.get('suggested_function') or primary.get('intent')
        primary_slots = primary.get('slots', {})
        
        # Merge all slots from all intents
        for intent in intents:
            intent_slots = intent.get('slots', {})
            for key, value in intent_slots.items():
                # Include ALL values, even None to show what was checked
                if key in all_extracted_slots:
                    # If key exists, handle merging
                    existing = all_extracted_slots[key]
                    if value is not None:  # Only merge non-null values
                        if isinstance(existing, list):
                            if isinstance(value, list):
                                # Merge two lists, avoid duplicates
                                for item in value:
                                    if item not in existing:
                                        existing.append(item)
                            elif value not in existing:
                                existing.append(value)
                        elif isinstance(value, list):
                            # Replace single value with list
                            all_extracted_slots[key] = value
                        elif existing != value and value is not None:
                            # Convert to list if different values
                            all_extracted_slots[key] = [existing, value]
                else:
                    # Add new key with its value
                    all_extracted_slots[key] = value
    
    # Handle clarification needed - but KEEP the extracted slots
    if extracted_data.get('followup') and extracted_data.get('clarify_question'):
        return {
            'function': 'ask_clarify',
            'text': extracted_data.get('clarify_question'),
            'params': primary_slots,  # Include primary slots
            'all_slots': all_extracted_slots,  # Include all extracted slots
            'missing_info': intents[0].get('missing_info', []) if intents else [],
            'suggested_function': primary_function  # Keep the intended function
        }
    
    # Handle empty/invalid response
    if not intents:
        return {
            'function': 'ask_clarify',
            'text': 'Could you please provide more details?',
            'error': 'No intent detected',
            'params': {},
            'all_slots': {}
        }
    
    return {
        'function': primary_function,
        'params': primary_slots,  # Slots from primary intent only
        'all_slots': all_extracted_slots,  # ALL extracted information from ALL intents
        'missing_info': intents[0].get('missing_info', [])  # What info is still needed
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


