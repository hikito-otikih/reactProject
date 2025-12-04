"""
Extract Info Module
Extracts journey planning information from natural language using Gemini API.

DEPRECATED: This module uses static dictionary-based optimization.
For maximum accuracy, use orchestrator.py with Two-Pass workflow instead.

Keeping this module for backward compatibility only.
"""

import json
import requests
import math
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from prompt_config import (
    DOMAIN_KEYWORDS,
    MODIFIER_KEYWORDS,
    FEW_SHOT_EXAMPLES,
    SCHEMA_SLOTS,
    VAGUE_LOCATION_KEYWORDS,
    VAGUE_CATEGORY_KEYWORDS
)

# Import the new orchestrator for comparison
from orchestrator import extract_info_with_orchestrator

load_dotenv()
GEOAPIFY_API_KEY = os.getenv('GEOAPIFY_KEY')
GEMINI_KEY = os.getenv('GEMINI_KEY')

# ============================================================================
# LEGACY FUNCTIONS (Token-Optimized, Lower Accuracy)
# Use orchestrator.py for production
# ============================================================================


def detect_domain(user_input):
    """
    Detect the primary domain(s) from user input using keyword matching.
    
    Returns:
        list: Detected domains in priority order
    """
    input_lower = user_input.lower()
    domain_scores = {domain: 0 for domain in DOMAIN_KEYWORDS}
    
    # Score each domain based on keyword matches
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in input_lower:
                domain_scores[domain] += 1
    
    # Check if it's a modification request
    is_modifier = any(keyword in input_lower for keyword in MODIFIER_KEYWORDS)
    
    # Sort domains by score
    sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Get domains with non-zero scores
    detected = [domain for domain, score in sorted_domains if score > 0]
    
    # Default to general if no specific domain detected
    if not detected or (detected[0] == 'modification' and len(detected) == 1):
        detected.append('general')
    
    return detected, is_modifier


def detect_vagueness(user_input):
    """
    Detect if user input contains vague location or category keywords.
    
    Parameters:
        user_input (str): User's input text
    
    Returns:
        tuple: (has_vague_location, has_vague_category, is_ambiguous)
    """
    input_lower = user_input.lower()
    
    has_vague_location = any(keyword in input_lower for keyword in VAGUE_LOCATION_KEYWORDS)
    has_vague_category = any(keyword in input_lower for keyword in VAGUE_CATEGORY_KEYWORDS)
    
    # Trigger clarification mode if both are present OR just vague category
    is_ambiguous = has_vague_category or (has_vague_location and has_vague_category)
    
    return has_vague_location, has_vague_category, is_ambiguous


def build_dynamic_schema(domains, is_ambiguous=False):
    """
    Build a JSON schema string with only relevant slots for detected domains.
    
    Parameters:
        domains (list): List of detected domain names
        is_ambiguous (bool): Whether ambiguity was detected
    
    Returns:
        str: JSON schema string
    """
    # Merge slots from all detected domains (excluding 'modification' and 'general')
    merged_slots = {}
    for domain in domains:
        if domain in SCHEMA_SLOTS and domain not in ['modification', 'general']:
            merged_slots.update(SCHEMA_SLOTS[domain])
    
    # If no specific domain, use general
    if not merged_slots:
        merged_slots = SCHEMA_SLOTS['general']
    
    # Build slots string
    slots_str = ', '.join([f'"{key}":{value}' for key, value in merged_slots.items()])
    
    # Add missing_info field for ambiguous cases
    missing_info_field = '"missing_info": [],' if is_ambiguous else ''
    clarify_question_field = '"clarify_question": null' if is_ambiguous else '"clarify_text": null'
    
    # Complete schema
    schema = f"""
    {{
        "intents": [
            {{
                "intent": "string",
                "suggested_function": "string",
                "confidence": 0.0,
                "slots": {{{slots_str}}},
                "entities": [{{"type":"string", "text":"string"}}],
                "keywords": [],
                {missing_info_field}
            }}
        ],
        "followup": false,
        {clarify_question_field}
    }}
    """
    
    return schema


def get_few_shot_examples(domains, is_ambiguous=False, max_examples=2):
    """
    Get relevant few-shot examples based on detected domains.
    
    Parameters:
        domains (list): List of detected domain names
        is_ambiguous (bool): Whether ambiguity was detected
        max_examples (int): Maximum number of examples to include
    
    Returns:
        str: Formatted examples string
    """
    examples = []
    
    # If ambiguous, prioritize clarification examples
    if is_ambiguous and 'clarification' in FEW_SHOT_EXAMPLES:
        examples.extend(FEW_SHOT_EXAMPLES['clarification'][:2])
    else:
        for domain in domains:
            if domain in FEW_SHOT_EXAMPLES:
                examples.extend(FEW_SHOT_EXAMPLES[domain][:1])  # 1 example per domain
        
        if not examples:
            examples = FEW_SHOT_EXAMPLES['general']
    
    # Limit total examples
    examples = examples[:max_examples]
    
    # Format examples
    examples_text = "\n\n".join([
        f"Example Input: \"{ex['input']}\"\nExpected Output:\n{json.dumps(ex['output'], indent=2)}"
        for ex in examples
    ])
    
    return examples_text


def build_context_string(conversation_history, is_modifier, max_messages=2):
    """
    Build context string from conversation history if needed.
    
    Parameters:
        conversation_history (list): List of {"role": "user/bot", "message": "..."}
        is_modifier (bool): Whether current input is a modification
        max_messages (int): Maximum number of recent messages to include
    
    Returns:
        str: Formatted context string or empty string
    """
    if not is_modifier or not conversation_history:
        return ""
    
    # Get last N messages
    recent_messages = conversation_history[-max_messages:]
    
    context = "\n\nRecent Conversation Context:\n"
    for msg in recent_messages:
        role = msg.get('role', 'unknown')
        message = msg.get('message', '')
        context += f"{role.capitalize()}: {message}\n"
    
    return context


def build_dynamic_prompt(user_input, conversation_history=None, previous_extracted_state=None):
    """
    Build an optimized, domain-aware prompt for the Travel Chatbot.
    
    Parameters:
        user_input (str): Current user message
        conversation_history (list): List of recent conversation messages
        previous_extracted_state (dict): Previously extracted state (for potential merging)
    
    Returns:
        str: Complete prompt string optimized for the current context
    """
    if not user_input or not user_input.strip():
        return None
    
    # Step 1: Check for vagueness/ambiguity
    has_vague_location, has_vague_category, is_ambiguous = detect_vagueness(user_input)
    
    # Step 2: Detect domain(s) and modifier status
    detected_domains, is_modifier = detect_domain(user_input)
    
    # Step 3: Build dynamic schema with ambiguity support
    schema = build_dynamic_schema(detected_domains, is_ambiguous)
    
    # Step 4: Get relevant few-shot examples (prioritize clarification if ambiguous)
    examples = get_few_shot_examples(detected_domains, is_ambiguous, max_examples=2)
    
    # Step 5: Build context if needed
    context = build_context_string(
        conversation_history or [], 
        is_modifier, 
        max_messages=2
    )
    
    # Step 6: Build ambiguity rule if needed
    ambiguity_rule = ""
    if is_ambiguous:
        ambiguity_rule = """

**AMBIGUITY RULE:**
If the user asks for general recommendations (e.g., "things to do") without specifying a category (like "food", "museums", "parks"), you MUST set the intent to "ask_clarify". Do NOT guess a category. Return a "clarify_question" asking for their preference. Include the specific missing information in the "missing_info" array (e.g., ["category"]).
"""
    
    # Step 7: Assemble the complete prompt
    prompt = f"""You are a structured extractor for a Travel Chatbot. Your task is to parse user messages and return ONLY valid JSON with no additional text or explanations.

DETECTED DOMAINS: {', '.join(detected_domains)}
AMBIGUITY DETECTED: {is_ambiguous}

JSON SCHEMA:
{schema}

RULES:
1. Return ONLY valid JSON matching the schema above.
2. Support multiple intents in the "intents" array for compound requests (e.g., "book flight and hotel").
3. Set fields to null if unknown or not mentioned.
4. If critical information is missing, set followup=true and provide clarify_question.
5. Extract all relevant entities (LOCATION, DATE, MONEY, NUMBER, PREFERENCES).
6. Confidence should be 0.0-1.0 based on clarity and completeness.
7. Suggested functions: search_hotels, book_hotel, search_flights, book_flight, suggest_itinerary, get_attractions, ask_clarify, greet, farewell, faq_answer.{ambiguity_rule}

FEW-SHOT EXAMPLES:
{examples}
{context}

USER INPUT: "{user_input}"

Now extract the JSON:
"""
    
    return prompt

def extract_info(text, conversation_history=None, previous_state=None): 
    """
    Extract key information from user text using Gemini API with dynamic prompt optimization.

    Parameters:
        text (str): User input text describing the journey/request.
        conversation_history (list): Recent conversation messages for context.
        previous_state (dict): Previously extracted state for potential merging.
    
    Returns:
        dict: Extracted information in JSON format with intents, slots, entities, etc.
    """
    if not text or not text.strip():
        return {
            'intents': [],
            'followup': True,
            'clarify_text': 'Please provide more information about your travel plans.'
        }
    
    try: 
        # Build dynamic prompt based on context
        prompt = build_dynamic_prompt(text, conversation_history, previous_state)

        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}'
        
        headers = {
            'Content-Type': 'application/json'
        }
         
        data = {
            'contents': [{
                'parts': [{
                    'text': prompt
                }]
            }],
            'generationConfig': {
                'temperature': 0.1,
                'topP': 0.8,
                'topK': 40,
                'maxOutputTokens': 8192,
                'responseMimeType': 'application/json'
            },
            'systemInstruction': {
                'parts': [{
                    'text': 'You are a JSON extraction assistant. Return only valid JSON with no additional text or explanation.'
                }]
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=40)
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result['candidates'][0]['content']['parts'][0]['text']
            extracted_info = json.loads(generated_text)
            return extracted_info
        else:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        if 'generated_text' in locals():
            print(f"Generated text was: {generated_text}")
    except Exception as e:
        print(f"Error extracting info with Gemini: {e}")


# Example usage and testing
if __name__ == "__main__":
    print("="*70)
    print("NOTICE: This is the LEGACY token-optimized version.")
    print("For MAXIMUM ACCURACY, use: python orchestrator.py")
    print("="*70)
    print("\nChoose mode:")
    print("1. Legacy (faster, token-optimized, lower accuracy)")
    print("2. Orchestrator (slower, ACCURACY FIRST)")
    
    mode = input("\nSelect mode (1/2, default=2): ").strip() or "2"
    
    if mode == "2":
        print("\n🎯 Using Two-Pass Orchestrator (ACCURACY FIRST)\n")
        print("="*70 + "\n")
        
        # Run orchestrator tests
        test_cases = [
            "What is there to do around here?",
            "Book a hotel in Paris for 3 nights",
            "Find museums near me",
            "Plan a 3-day trip to Rome with museums and restaurants"
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            print(f"Test {i}: {test_input}")
            result = extract_info_with_orchestrator(test_input)
            print(json.dumps(result, indent=2))
            print("\n" + "="*70 + "\n")
        
        # Interactive mode with orchestrator
        print("Interactive Mode - ORCHESTRATOR (type 'quit' to exit):")
        conversation = []
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            result = extract_info_with_orchestrator(user_input, conversation_history=conversation)
            print("\nExtracted:")
            print(json.dumps(result, indent=2))
            
            # Update conversation history
            conversation.append({"role": "user", "message": user_input})
            clarify_q = result.get('clarify_question')
            if clarify_q:
                conversation.append({"role": "bot", "message": clarify_q})
    
    else:
        print("\n⚠️  Using Legacy Mode (Token-Optimized)\n")
        print("="*70 + "\n")
        
        # Legacy tests
        print("Test 1: Ambiguous request (should trigger clarification)")
        result1 = extract_info("What is there to do around here?")
        print(json.dumps(result1, indent=2))
        print("\n" + "="*50 + "\n")
        
        print("Test 2: Vague location and category")
        result2 = extract_info("Show me things to do nearby")
        print(json.dumps(result2, indent=2))
        print("\n" + "="*50 + "\n")
        
        print("Test 3: Specific request (no clarification needed)")
        result3 = extract_info("Find museums near me")
        print(json.dumps(result3, indent=2))
        print("\n" + "="*50 + "\n")
        
        print("Test 4: Simple hotel booking")
        result4 = extract_info("Book a hotel in Paris for 3 nights")
        print(json.dumps(result4, indent=2))
        print("\n" + "="*50 + "\n")
        
        # Interactive mode legacy
        print("Interactive Mode - LEGACY (type 'quit' to exit):")
        conversation = []
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
        
        result = extract_info(user_input, conversation_history=conversation)
        print("\nExtracted:")
        print(json.dumps(result, indent=2))
        
        # Update conversation history
        conversation.append({"role": "user", "message": user_input})
        clarify_q = result.get('clarify_question') or result.get('clarify_text')
        if clarify_q:
            conversation.append({"role": "bot", "message": clarify_q})

