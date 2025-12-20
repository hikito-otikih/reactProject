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
    
    # Build collected information context (compact format)
    collected_info_str = ""
    if collected_information:
        collected_info_str = "\n\nCOLLECTED INFO:\n"
        collected_info_str += json.dumps(collected_information, ensure_ascii=False)
    
    # Build conversation history context (last 5 messages only to reduce prompt length)
    context_str = ""
    if conversation_history:
        num_messages = min(5, len(conversation_history))  # Reduced from 10 to 5
        context_str = f"\n\nRECENT CONVERSATION (last {num_messages} messages):\n"
        for msg in conversation_history[-num_messages:]:
            role = msg.get('role', 'unknown')
            message = msg.get('message', '')
            context_str += f"{role}: {message}\n"
    
    print("user input for extraction:", user_input)
    # Simplified schema - only essential fields
    schema = """
    {
        "intents": [
            {
                "intent": "string",
                "suggested_function": "string",
                "slots": {
                    "destination": null,
                    "categories": [],
                    "limit": null
                }
            }
        ],
        "context_action": "merge",
        "followup": false,
        "clarify_question": null
    }
    """
    
    # Build few-shot examples
    examples = _build_relevant_examples()
    
    extraction_prompt = f"""Extract travel information from user query into JSON format.

SCHEMA:
{schema}

FUNCTIONS:
- itinerary_planning: Plan trip itinerary (needs limit, categories optional)
- suggest_categories: Suggest place categories
- suggest_attractions: Suggest specific attractions
- search_by_name: Search place by name
- ask_clarify: Ask for clarification

FIELDS:
- destination: City/area (e.g., "Hanoi", "Ho Chi Minh City")
- categories: List of place types (e.g., ["museum", "cafe", "park"])
- limit: Number of places (integer)
- context_action: How to handle collected info
  * "merge": Add to existing collected info (default)
  * "reset": Clear all collected info and start fresh
  * "replace": Replace specific fields only

RULES:
- Extract destination, categories, limit from query
- Set followup=true if info is missing
- Use COLLECTED INFO and HISTORY to avoid redundant questions
- Set context_action="reset" if user changes topic completely (e.g., "actually, let's go somewhere else" or "never mind, I want to visit a different place")
- Set context_action="merge" for adding/refining current context
- Set context_action="replace" when user corrects previous information
{examples}
{collected_info_str}
{context_str}

USER QUERY: "{user_input}"
"""

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
                'temperature': 0.1,
                'topP': 0.95,
                'topK': 40,
                'maxOutputTokens': 2500,  # Increased to prevent truncation
                'responseMimeType': 'application/json',
                'candidateCount': 1
            },
            'systemInstruction': {
                'parts': [{
                    'text': 'You are a JSON extraction expert. Return only valid JSON. No explanations.'
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
            
            # Enhanced logging to debug JSON parsing issues
            print(f"📡 Gemini API Response Status: 200")
            print(f"🔍 Full API response structure: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
            
            # Check if response has expected structure
            if 'candidates' not in result or not result['candidates']:
                print(f"⚠️ No candidates in response - likely blocked by safety filters")
                return {
                    'intents': [],
                    'followup': True,
                    'clarify_question': 'I had trouble processing that. Could you rephrase?'
                }
            
            extracted_text = result['candidates'][0]['content']['parts'][0]['text']
            print(f"📄 Raw extracted text:\n{extracted_text}\n")
            
            # Clean and extract JSON from response
            extracted_info = _parse_json_response(extracted_text, user_input)
            return extracted_info
        else:
            raise Exception(f"Gemini API error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error in information extraction: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Log more details for debugging
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"Response text: {e.response.text[:500] if hasattr(e.response, 'text') else 'N/A'}")
        
        return {
            'intents': [],
            'followup': True,
            'clarify_question': 'I encountered an error processing your request. Could you please rephrase?',
            'error': str(e)
        }


def _parse_json_response(text, user_input):
    """
    Parse JSON from LLM response with robust error handling.
    Handles markdown code blocks, extra text, and malformed JSON.
    
    Parameters:
        text (str): Raw text response from LLM
        user_input (str): Original user input for fallback
    
    Returns:
        dict: Parsed JSON or fallback response
    """
    import re
    
    # Strategy 1: Try direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract JSON from markdown code blocks
    # Match ```json\n{...}\n``` or ```\n{...}\n```
    code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(code_block_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Strategy 3: Find JSON object using regex (find first { to last })
    json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\})*)*\}))*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    if matches:
        # Try the longest match first (likely the complete JSON)
        for match in sorted(matches, key=len, reverse=True):
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    
    # Strategy 4: Clean common issues and retry
    cleaned = text.strip()
    # Remove common prefixes
    for prefix in ['json\n', 'JSON\n', 'Here is the JSON:\n', 'Output:\n']:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parsing failed after all strategies")
        print(f"Raw response (first 500 chars):\n{text[:500]}")
        print(f"JSON Error: {e}")
    
    # Final fallback: Return safe default
    return {
        'intents': [{
            'intent': 'search_by_name',
            'suggested_function': 'search_by_name',
            'confidence': 0.5,
            'slots': {
                'destination': user_input,
                'categories': None,
                'limit': None
            }
        }],
        'followup': False,
        'clarify_question': None
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
    
    # Normalize field names from LLM output
    result = _normalize_field_names(result)
    
    # Load valid categories from categories.txt
    categories_file_path = os.path.join(os.path.dirname(__file__), 'categories.txt')
    valid_categories = []
    try:
        with open(categories_file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            valid_categories = [cat.strip() for cat in content.split(',')]
    except Exception as e:
        print(f"⚠️ Could not load categories.txt: {e}")
    
    # Match and replace categories in the result
    if valid_categories and 'intents' in result:
        for intent in result['intents']:
            if 'slots' in intent and 'categories' in intent['slots']:
                categories = intent['slots']['categories']
                if categories and isinstance(categories, list):
                    matched_categories = []
                    for cat in categories:
                        if cat:
                            # Find the best match from valid_categories
                            best_match = _find_best_category_match(cat, valid_categories)
                            if best_match:
                                matched_categories.append(best_match)
                                print(f"📝 Matched '{cat}' -> '{best_match}'")
                            else:
                                matched_categories.append(cat)  # Keep original if no match found
                    intent['slots']['categories'] = matched_categories
    
    return result


def _normalize_field_names(result):
    """
    Normalize field names from LLM output to standard format.
    Maps various field name aliases to standard names:
    - destination: place_name, location, place, attraction_name, name
    - categories: category, types, place_types
    - limit: number, count, num_places, number_of_places
    
    Parameters:
        result (dict): Raw result from LLM
    
    Returns:
        dict: Result with normalized field names
    """
    if not isinstance(result, dict) or 'intents' not in result:
        return result
    
    # Field name mappings - order matters: higher priority first
    destination_aliases = ['place_name', 'attraction_name', 'name', 'location', 'place', 'destination_name']
    categories_aliases = ['category', 'types', 'place_types', 'type', 'place_type']
    limit_aliases = ['number', 'count', 'num_places', 'number_of_places', 'num']
    
    for intent in result['intents']:
        if 'slots' not in intent:
            continue
            
        slots = intent['slots']
        
        # Normalize destination - prioritize place_name over destination
        # If both exist, place_name takes precedence
        if 'place_name' in slots and slots['place_name']:
            slots['destination'] = slots['place_name']
            print(f"🔄 Prioritized 'place_name' -> 'destination': {slots['place_name']}")
        elif 'destination' not in slots or not slots['destination']:
            for alias in destination_aliases:
                if alias in slots and slots[alias]:
                    slots['destination'] = slots[alias]
                    print(f"🔄 Normalized '{alias}' -> 'destination': {slots[alias]}")
                    break
        
        # Normalize categories
        if 'categories' not in slots or not slots['categories']:
            for alias in categories_aliases:
                if alias in slots and slots[alias]:
                    # Convert single value to list
                    if isinstance(slots[alias], str):
                        slots['categories'] = [slots[alias]]
                    elif isinstance(slots[alias], list):
                        slots['categories'] = slots[alias]
                    print(f"🔄 Normalized '{alias}' -> 'categories': {slots['categories']}")
                    break
        
        # Normalize limit
        if 'limit' not in slots or not slots['limit']:
            for alias in limit_aliases:
                if alias in slots and slots[alias]:
                    try:
                        slots['limit'] = int(slots[alias])
                        print(f"🔄 Normalized '{alias}' -> 'limit': {slots['limit']}")
                        break
                    except (ValueError, TypeError):
                        pass
    
    return result


def _find_best_category_match(input_category, valid_categories):
    """
    Find the best matching category from the valid categories list.
    Enhanced with translation and plural/singular handling.
    
    Parameters:
        input_category (str): Category extracted from user input
        valid_categories (list): List of valid categories from categories.txt
    
    Returns:
        str: Best matching category or None if no good match found
    """
    if not input_category or not valid_categories:
        return None
    
    input_lower = input_category.lower().strip()
    
    # Generate variants of the input category
    variants = _generate_category_variants(input_lower)
    
    # Try exact match with all variants
    for variant in variants:
        if variant in valid_categories:
            return variant
    
    # Partial match - check if any variant is contained in valid category or vice versa
    for variant in variants:
        for valid_cat in valid_categories:
            if variant in valid_cat or valid_cat in variant:
                return valid_cat
    
    # Use difflib for fuzzy matching with all variants
    from difflib import get_close_matches
    for variant in variants:
        matches = get_close_matches(variant, valid_categories, n=1, cutoff=0.6)
        if matches:
            return matches[0]
    
    return None


def _generate_category_variants(input_category):
    """
    Generate variants of input category including:
    - Original
    - Translated (Vietnamese <-> English)
    - Plural/Singular forms
    
    Parameters:
        input_category (str): Original category string
    
    Returns:
        list: List of category variants
    """
    variants = set()
    input_lower = input_category.lower().strip()
    variants.add(input_lower)
    
    # Add plural/singular variants
    variants.update(_get_plural_singular_variants(input_lower))
    
    # Try translation Vietnamese -> English
    try:
        translated_en = translate(input_category, target_language='en')
        if translated_en and translated_en.lower() != input_lower:
            translated_en_lower = translated_en.lower().strip()
            variants.add(translated_en_lower)
            # Add plural/singular of translated English
            variants.update(_get_plural_singular_variants(translated_en_lower))
    except Exception as e:
        print(f"⚠️ Translation to English failed: {e}")
    
    # Try translation English -> Vietnamese
    try:
        translated_vi = translate(input_category, target_language='vi')
        if translated_vi and translated_vi.lower() != input_lower:
            translated_vi_lower = translated_vi.lower().strip()
            variants.add(translated_vi_lower)
            # Translate Vietnamese back to English for more variants
            try:
                back_translated = translate(translated_vi, target_language='en')
                if back_translated:
                    back_translated_lower = back_translated.lower().strip()
                    variants.add(back_translated_lower)
                    variants.update(_get_plural_singular_variants(back_translated_lower))
            except:
                pass
    except Exception as e:
        print(f"⚠️ Translation to Vietnamese failed: {e}")
    
    return list(variants)


def _get_plural_singular_variants(word):
    """
    Generate plural and singular variants of an English word.
    
    Parameters:
        word (str): Input word
    
    Returns:
        set: Set of variants (plural and singular forms)
    """
    variants = set()
    word_lower = word.lower().strip()
    
    # Rules for plural -> singular
    if word_lower.endswith('ies'):
        # galleries -> gallery, bakeries -> bakery
        variants.add(word_lower[:-3] + 'y')
    elif word_lower.endswith('ses'):
        # churches -> church, boxes -> box
        variants.add(word_lower[:-2])
    elif word_lower.endswith('shes') or word_lower.endswith('ches'):
        # dishes -> dish, churches -> church
        variants.add(word_lower[:-2])
    elif word_lower.endswith('s') and not word_lower.endswith('ss'):
        # museums -> museum, cafes -> cafe
        variants.add(word_lower[:-1])
    
    # Rules for singular -> plural
    if word_lower.endswith('y') and len(word_lower) > 1 and word_lower[-2] not in 'aeiou':
        # gallery -> galleries, bakery -> bakeries
        variants.add(word_lower[:-1] + 'ies')
    elif word_lower.endswith(('s', 'x', 'z', 'ch', 'sh')):
        # church -> churches, box -> boxes
        variants.add(word_lower + 'es')
    elif not word_lower.endswith('s'):
        # museum -> museums, cafe -> cafes
        variants.add(word_lower + 's')
    
    return variants


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
