"""
End-to-end pipeline: User Input → Function Call
Combines orchestrator, translator, and formatter for complete processing.
"""

import json
from orchestrator import extract_info_with_orchestrator
from translator import translate, detectLanguage
from function_dispatcher import format_llm_response


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
    
    # Translate location names back to source language if needed
    if source_language and source_language != 'en' and 'params' in result:
        _translate_locations_back(result['params'], source_language)
    
    return result


def _translate_locations_back(params: dict, target_language: str):
    """Translate location-related fields back to source language."""
    location_fields = ['destination', 'start_location', 'location', 'attraction_name']
    
    for field in location_fields:
        if field in params and params[field]:
            if isinstance(params[field], str):
                params[field] = translate(params[field], target_language=target_language)
            elif isinstance(params[field], list):
                params[field] = [
                    translate(item, target_language=target_language) if isinstance(item, str) else item
                    for item in params[field]
                ]


# Example usage
if __name__ == "__main__":
    print("=== End-to-End User Input Processing ===\n")
    
    test_cases = [
        {
            'input': "Tôi muốn tham quan bảo tàng ở quận 1",
            'history': None
        },
        {
            'input': "Lên kế hoạch đi vòng quanh hồ gươm và thưởng thức ẩm thực đường phố trong một ngày",
            'history': None
        },
        {
            'input': "Quanh đây có gì chơi không?",
            'history': None
        },
        {
            'input': "Show me details about Ben Thanh Market",
            'history': None
        },
        {
            'input': "I want to visit museums and cafes",
            'history': [
                {'role': 'user', 'message': 'I want to plan a trip'},
                {'role': 'bot', 'message': 'Where would you like to start from?'},
                {'role': 'user', 'message': 'HCMUS'}
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['input']}")
        result = process_user_input(test_case['input'], test_case['history'])
        print("Output:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n" + "="*70 + "\n")
