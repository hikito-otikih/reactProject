"""
LLM Response Formatter
Converts LLM extraction output to clean, readable format for your team.

Simple transformer: LLM dictionary → Human-readable structured data
"""

import json
from typing import Dict, Any, List


def format_llm_response(extracted_data: Dict) -> Dict:
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


# Example usage
if __name__ == "__main__":
    print("=== LLM Response Formatter Test ===\n")
    
    # Test 1: Normal itinerary request
    llm_output_1 = {
        'intents': [{
            'intent': 'create_itinerary',
            'suggested_function': 'suggest_itinerary',
            'confidence': 0.9,
            'slots': {
                'start_location': 'HCMUS',
                'categories': ['museum', 'restaurant'],
                'duration_days': 1
            },
            'entities': [
                {'type': 'LOCATION', 'text': 'HCMUS'}
            ]
        }],
        'followup': False
    }
    
    result_1 = format_llm_response(llm_output_1)
    print("Test 1 - Itinerary Request:")
    print(json.dumps(result_1, indent=2))
    print("\n" + "="*70 + "\n")
    
    # Test 2: Clarification needed
    llm_output_2 = {
        'intents': [{
            'intent': 'ask_clarify',
            'suggested_function': 'ask_clarify',
            'confidence': 1.0,
            'slots': {}
        }],
        'followup': True,
        'clarify_question': 'What type of places are you interested in?'
    }
    
    result_2 = format_llm_response(llm_output_2)
    print("Test 2 - Clarification:")
    print(json.dumps(result_2, indent=2))
    print("\n" + "="*70 + "\n")
    
    # Test 3: Get attraction details
    llm_output_3 = {
        'intents': [{
            'intent': 'get_details',
            'suggested_function': 'get_attraction_details',
            'confidence': 0.85,
            'slots': {
                'attraction_name': 'Ben Thanh Market'
            },
            'entities': [
                {'type': 'LOCATION', 'text': 'Ben Thanh Market'}
            ]
        }],
        'followup': False
    }
    
    result_3 = format_llm_response(llm_output_3)
    print("Test 3 - Attraction Details:")
    print(json.dumps(result_3, indent=2))
