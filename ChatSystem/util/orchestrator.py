"""
Single-Pass Information Extraction
Context-aware LLM call with conversation history and collected information
"""

import json
import requests
import os
from dotenv import load_dotenv
from .translator import translate, detectLanguage

load_dotenv()
GEMINI_KEY = os.getenv('GEMINI_KEY')


def extract_information_single_pass(user_input, collected_information=None, conversation_history=None):
    """
    Single-pass information extraction from user query.
    
    Parameters:
        user_input (str): User's query
        collected_information (dict): Previously collected slot data
        conversation_history (list): Recent conversation messages
    
    Returns:
        dict: Extracted information in JSON format
    """
    
    # Build collected information context
    collected_info_str = ""
    if collected_information:
        collected_info_str = "\n\nCOLLECTED INFORMATION (from previous interactions):\n"
        collected_info_str += json.dumps(collected_information, indent=2, ensure_ascii=False)
        collected_info_str += "\n\nIMPORTANT: Use this information to understand what's already known. Do NOT ask for information already present. Focus on extracting NEW or MISSING information only.\n"
    
    # Build conversation history context (last 5-10 messages)
    context_str = ""
    if conversation_history:
        num_messages = min(10, len(conversation_history))
        context_str = f"\n\nRECENT CONVERSATION HISTORY (last {num_messages} messages):\n"
        for msg in conversation_history[-num_messages:]:
            role = msg.get('role', 'unknown')
            message = msg.get('message', '')
            context_str += f"{role}: {message}\n"
        context_str += "\nUse this context to better understand the current query and maintain conversation continuity.\n"
    
    # Simplified schema - only essential fields
    schema = """
    {
        "intents": [
            {
                "intent": "string",
                "suggested_function": "string",
                "confidence": 0.0,
                "slots": {
                    "destination": null,
                    "categories": [],
                    "limit": null
                }
            }
        ],
        "followup": false,
        "clarify_question": null
    }
    """
    
    # Build few-shot examples
    examples = _build_relevant_examples()
    
    extraction_prompt = f"""You are a Travel Information Extraction Expert. Extract structured data from user queries with MAXIMUM ACCURACY.

REQUIRED JSON SCHEMA:
{schema}

EXTRACTION RULES:
1. Return ONLY valid JSON matching the schema above. No additional text.
2. Extract all entities mentioned in the query (LOCATION, CATEGORIES, NUMBER).
3. Set confidence based on completeness and clarity (0.0 to 1.0).
4. If information is unclear or missing, set followup=true and provide a clarify_question.

5. Available functions and their purposes:
   - suggest_from_database: Suggest attractions from database when destination and categories are known
   - itinerary_planning: Create complete trip itinerary with locations and timing
   - suggest_categories: Suggest place categories based on user context
   - suggest_attractions: Suggest attractions of given category
   - get_attraction_details: Display attraction details (image, description, opening hours, ticket price)
   - ask_clarify: Ask for clarification when info is missing

6. SCHEMA FIELDS (only these are tracked):
   - destination (string): The city or area to visit (e.g., "Ho Chi Minh City", "Hanoi")
   - categories (list): Types of attractions (e.g., ["museums", "nature", "food"])
   - limit (integer): Number of attractions to visit (default: 3)

7. CONTEXT AWARENESS:
   - Pay careful attention to COLLECTED INFORMATION to avoid asking redundant questions
   - Use CONVERSATION HISTORY to understand references like "there", "it", "that place"
   - If user mentions "nearby", "around here", set destination to "current_location"

8. AMBIGUITY HANDLING:
   - If category is vague ("things to do", "fun stuff"), set intent to "ask_clarify"
   - If destination is missing and not in collected info, ask for it
   - If user asks general questions without specifics, provide helpful clarification
{examples}
{collected_info_str}
{context_str}

USER QUERY: "{user_input}"

EXTRACT THE JSON NOW:"""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}'
        
        headers = {'Content-Type': 'application/json'}
        
        data = {
            'contents': [{
                'parts': [{
                    'text': extraction_prompt
                }]
            }],
            'generationConfig': {
                'temperature': 0.0,  # Maximum determinism for accuracy
                'topP': 0.95,  # Higher nucleus sampling for better quality
                'topK': 40,
                'maxOutputTokens': 3072,  # Increased for complex responses
                'responseMimeType': 'application/json',
                'candidateCount': 1,  # Single best response
                'stopSequences': []  # No stop sequences
            },
            'systemInstruction': {
                'parts': [{
                    'text': 'You are a precision JSON extraction expert. Return only valid JSON with maximum accuracy. No explanations. Pay close attention to collected information and conversation history. Always validate your output against the schema before responding.'
                }]
            },
            'safetySettings': [
                {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_NONE'},
                {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_NONE'},
                {'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'threshold': 'BLOCK_NONE'},
                {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_NONE'}
            ]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=40)
        
        if response.status_code == 200:
            result = response.json()
            extracted_text = result['candidates'][0]['content']['parts'][0]['text']
            extracted_info = json.loads(extracted_text)
            return extracted_info
        else:
            raise Exception(f"Gemini API error: {response.status_code}")
    
    except Exception as e:
        #print(GEMINI_KEY)
        print(f"Error in information extraction: {e}")
        return {
            'intents': [],
            'followup': True,
            'clarify_question': 'I encountered an error processing your request. Could you please rephrase?',
            'error': str(e)
        }


def _build_relevant_examples():
    """Build relevant few-shot examples."""
    from .prompt_config import FEW_SHOT_EXAMPLES
    
    examples_text = "\n\nEXAMPLES:\n"
    
    # Include one example from each important category
    example_types = ['itinerary', 'clarification', 'general']
    
    for ex_type in example_types:
        if ex_type in FEW_SHOT_EXAMPLES and FEW_SHOT_EXAMPLES[ex_type]:
            ex = FEW_SHOT_EXAMPLES[ex_type][0]
            examples_text += f"\nInput: \"{ex['input']}\"\nOutput:\n{json.dumps(ex['output'], indent=2)}\n"
    
    return examples_text


def generate_dynamic_suggestions(context, question, num_suggestions=3):
    """
    Generate dynamic suggestions using LLM based on conversation context.
    
    Parameters:
        context (str): Current conversation context
        question (str): The question being asked to the user
        num_suggestions (int): Number of suggestions to generate
    
    Returns:
        list: List of suggested responses
    """
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}'
    
    prompt = f"""Based on the following context and question, generate {num_suggestions} relevant, helpful, and diverse response suggestions that a user might want to choose from.

Context: {context}
Question: {question}

Generate exactly {num_suggestions} short, natural suggestions (each 3-8 words). Return ONLY a JSON array of strings, nothing else.

Example format: ["suggestion 1", "suggestion 2", "suggestion 3"]"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.8,  # Slightly higher for diversity in suggestions
            "topP": 0.95,
            "topK": 40,
            "maxOutputTokens": 300,
            "candidateCount": 1
        },
        "safetySettings": [
            {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_NONE'},
            {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_NONE'},
            {'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'threshold': 'BLOCK_NONE'},
            {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_NONE'}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        text = result['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Extract JSON array from response
        import re
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            suggestions = json.loads(json_match.group())
            return suggestions[:num_suggestions]
        
    except Exception as e:
        print(f"⚠️  Dynamic suggestion generation failed: {e}")
    
    # Fallback suggestions
    return ["Tell me more", "Skip this", "Continue"]


def extract_info_with_orchestrator(user_input, collected_information, conversation_history=None):
    """
    Main orchestrator function implementing single-pass extraction.
    
    Parameters:
        user_input (str): User's query
        collected_information (dict): Previously collected slot data
        conversation_history (list): Recent conversation messages
    
    Returns:
        dict: Extracted information in JSON format
    """
    
    if not user_input or not user_input.strip():
        return {
            'intents': [],
            'followup': True,
            'clarify_question': 'Please provide more information about your travel plans.'
        }
    
    print("🔍 Extracting information...")
    result = extract_information_single_pass(user_input, collected_information, conversation_history)
    print("✅ Extraction complete\n")
    
    return result


# Example usage
if __name__ == "__main__":
    print("=== Single-Pass Information Extraction Testing ===\n")
    
    test_cases = [
        "Tôi muốn tham gia buổi hoà nhạc?",
        "Lên kế hoạch đi vòng quanh hồ gươm và thưởng thức ẩm thực đường phố trong một ngày.",
        "Đi vòng quanh thành phố Hồ Chí Minh, lai rai mấy quán cà phê đẹp và các điểm tham quan lịch sử.",
    ]
    
    # Simulate conversation with collected info
    collected_info = {}
    conversation_history = []
    
    for i, test_input in enumerate(test_cases, 1):
        srcLanguage = detectLanguage(test_input)
        english_input = translate(test_input, target_language='en')
        print(f"Test {i}: {english_input}")
        
        result = extract_info_with_orchestrator(english_input, collected_info, conversation_history)
        
        # Translate location names back to Vietnamese for display
        if 'intents' in result:
            for intent in result['intents']:
                if 'slots' in intent and 'destination' in intent['slots'] and intent['slots']['destination']:
                    intent['slots']['destination'] = translate(intent['slots']['destination'], target_language=srcLanguage)
        
        print(json.dumps(result, indent=2))
        print("\n" + "="*70 + "\n")
        
        # Update conversation history
        conversation_history.append({'role': 'user', 'message': english_input})
        conversation_history.append({'role': 'assistant', 'message': result.get('clarify_question', 'Processed')})
