"""
Two-Pass Orchestrator Workflow
ACCURACY FIRST POLICY - No token optimization, maximum precision

Pass 1: Analysis - Dynamically analyze context and define requirements
Pass 2: Execution - Generate accurate response based on Pass 1 analysis
"""

import json
import requests
import os
from dotenv import load_dotenv
from .translator import translate, detectLanguage

load_dotenv()
GEMINI_KEY = os.getenv('GEMINI_KEY')


def pass1_analyze_query(user_input, collected_information=None, conversation_history=None):
    collected_info_str = ""
    if collected_information:
        collected_info_str = "\n\nCOLLECTED INFORMATION (from previous interactions):\n"
        collected_info_str += json.dumps(collected_information, indent=2, ensure_ascii=False)
        collected_info_str += "\n\nIMPORTANT: Use this information to better understand what's missing and what's already known.\n"
    
    context_str = ""
    if conversation_history:
        context_str = "\n\nRecent Conversation:\n"
        for msg in conversation_history[-5:]:
            context_str += f"{msg.get('role', 'unknown')}: {msg.get('message', '')}\n"

    analysis_prompt = f"""You are a Query Analysis Expert for a Travel Chatbot. Your ONLY job is to analyze the user's query and provide strategic recommendations for how to process it.
DO NOT attempt to answer the user's query. Only analyze it.
{collected_info_str}
{context_str}
USER QUERY: "{user_input}"
Provide a detailed analysis in JSON format:
{{
  "query_type": "string",  // e.g., "attractions_search", "itinerary_planning", "clarification_needed", "answer_previous_question", "general_inquiry", etc.
  "complexity": "low|medium|high",
  "domains_involved": ["domain1", "domain2"],  // e.g., ["accommodation", "transport"]
  "is_ambiguous": true/false,
  "ambiguity_reasons": ["reason1", "reason2"],  // What's unclear?
  "missing_information": ["field1", "field2"],  // What data is missing?
  "context_dependency": true/false,  // Does this rely on previous messages?
  "history_traverse_necessary": true/false,  // Should we look through conversation history to answer this?
  "recommended_schema_fields": ["field1", "field2"],  // Which fields are relevant?
  "suggested_examples": ["example_id1", "example_id2"],  // Which examples would help?
  "clarification_needed": true/false,
  "suggested_clarification": "string or null",  // What to ask user?
  "special_handling": ["flag1", "flag2"],  // e.g., ["vague_location", "multi_intent"]
  "reasoning": "string"  // Explain your analysis
}}

CRITICAL: Return ONLY the JSON. No additional text."""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}'
        
        headers = {'Content-Type': 'application/json'}
        
        data = {
            'contents': [{
                'parts': [{
                    'text': analysis_prompt
                }]
            }],
            'generationConfig': {
                'temperature': 0.1,  # Lower temperature for more consistent analysis
                'topP': 0.9,
                'topK': 40,
                'maxOutputTokens': 2048,
                'responseMimeType': 'application/json'
            },
            'systemInstruction': {
                'parts': [{
                    'text': 'You are a query analysis expert. Analyze queries and provide strategic recommendations in JSON format. Do not answer queries, only analyze them.'
                }]
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=40)
        
        if response.status_code == 200:
            result = response.json()
            analysis_text = result['candidates'][0]['content']['parts'][0]['text']
            analysis = json.loads(analysis_text)
            return analysis
        else:
            raise Exception(f"Gemini API error in Pass 1: {response.status_code}")
    
    except Exception as e:
        print(f"Error in Pass 1 Analysis: {e}")
        # Return minimal safe analysis
        return {
            "query_type": "unknown",
            "complexity": "medium",
            "domains_involved": ["general"],
            "is_ambiguous": False,
            "missing_information": [],
            "context_dependency": False,
            "recommended_schema_fields": [],
            "suggested_examples": [],
            "clarification_needed": False,
            "suggested_clarification": None,
            "special_handling": [],
            "confidence": 0.3,
            "reasoning": f"Analysis failed: {str(e)}"
        }

def pass2_generate_response(user_input, analysis, collected_information=None, conversation_history=None):
    """
    PASS 2: EXECUTION PHASE
    
    Generate the accurate response based on Pass 1 analysis.
    Uses the analysis to build a precision-optimized prompt.
    
    Parameters:
        user_input (str): User's query
        analysis (dict): Results from Pass 1
        collected_information (dict): Previously collected slot data
        conversation_history (list): Recent conversation context
    
    Returns:
        dict: Extracted information in precise JSON format
    """
    
    # Build dynamic schema based on analysis
    schema_fields = analysis.get('recommended_schema_fields', [])
    domains = analysis.get('domains_involved', ['general'])
    is_ambiguous = analysis.get('is_ambiguous', False)
    
    # Build schema dynamically
    slots = _build_slots_from_analysis(analysis)
    
    # Add special fields for ambiguous cases
    special_fields = ""
    if is_ambiguous:
        special_fields = '"missing_info": [],'
    
    schema = f"""
    {{
        "intents": [
            {{
                "intent": "string",
                "suggested_function": "string",
                "confidence": 0.0,
                "slots": {{{slots}}},
                {special_fields}
            }}
        ],
        "followup": {str(is_ambiguous).lower()},
        "clarify_question": null
    }}
    """
    
    # Build collected information context
    collected_info_str = ""
    if collected_information:
        collected_info_str = "\n\nCOLLECTED INFORMATION (already known):\n"
        collected_info_str += json.dumps(collected_information, indent=2, ensure_ascii=False)
        collected_info_str += "\n\nIMPORTANT: Do NOT ask for information already present above. Focus on extracting NEW or MISSING information only.\n"
    
    # Build context if needed
    context_str = ""
    if analysis.get('context_dependency') and conversation_history:
        context_str = "\n\nRECENT CONVERSATION CONTEXT:\n"
        for msg in conversation_history[-5:]:
            context_str += f"{msg.get('role', 'unknown')}: {msg.get('message', '')}\n"
    
    # Build special rules based on analysis
    special_rules = _build_special_rules(analysis)
    
    # Build examples based on analysis
    examples = _build_examples_from_analysis(analysis)
    
    execution_prompt = f"""You are a Travel Information Extraction Expert. Extract structured data from user queries with MAXIMUM ACCURACY.

REQUIRED JSON SCHEMA:
{schema}

EXTRACTION RULES:
1. Return ONLY valid JSON matching the schema above. No additional text.
2. Use the analysis insights to guide your extraction.
3. If information is missing (as identified in analysis), set fields to null.
4. Extract all entities mentioned in the query (LOCATION, DATE, MONEY, NUMBER, PREFERENCES).
5. Set confidence based on completeness and clarity.
6. Available functions and their purposes:
   - suggest_from_database: Suggest attractions from database when destination and categories are known
   - itinerary_planning: Create complete trip itinerary with locations and timing
   - suggest_categories: Suggest place categories based on user context 
   - suggest_attractions: Suggest attractions of given category
   - get_attraction_details: Display attraction details (image, description, opening hours, ticket price)
   - ask_clarify: Ask for clarification when info is missing
   
7. IMPORTANT - Collected Information Fields:
   - destination (string): The city or area to visit
   - categories (list): Types of attractions (e.g., ['museums', 'nature', 'food'])
   - limit (integer): Number of attractions to visit (default: 3)
   
8. NOTE: start_location, budget, duration_days, and dates are NOT tracked in collected_information
   as they are handled by the frontend or no longer needed.
{special_rules}

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
                    'text': execution_prompt
                }]
            }],
            'generationConfig': {
                'temperature': 0.1,  # Very low for maximum consistency
                'topP': 0.8,
                'topK': 40,
                'maxOutputTokens': 4096,
                'responseMimeType': 'application/json'
            },
            'systemInstruction': {
                'parts': [{
                    'text': 'You are a precision JSON extraction expert. Return only valid JSON with maximum accuracy. No explanations.'
                }]
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=40)
        
        if response.status_code == 200:
            result = response.json()
            extracted_text = result['candidates'][0]['content']['parts'][0]['text']
            extracted_info = json.loads(extracted_text)
            
            # Enrich with analysis metadata
            extracted_info['_analysis'] = {
                'query_type': analysis.get('query_type'),
                'complexity': analysis.get('complexity'),
                'confidence': analysis.get('confidence')
            }
            
            return extracted_info
        else:
            raise Exception(f"Gemini API error in Pass 2: {response.status_code}")
    
    except Exception as e:
        print(f"Error in Pass 2 Execution: {e}")
        return {
            'intents': [],
            'followup': True,
            'clarify_question': 'I encountered an error processing your request. Could you please rephrase?',
            'error': str(e)
        }

def _build_slots_from_analysis(analysis):
    """Build schema slots based on analysis recommendations."""
    from .prompt_config import SCHEMA_SLOTS
    
    domains = analysis.get('domains_involved', ['general'])
    merged_slots = {}
    
    for domain in domains:
        if domain in SCHEMA_SLOTS:
            merged_slots.update(SCHEMA_SLOTS[domain])
    
    if not merged_slots:
        merged_slots = SCHEMA_SLOTS.get('general', {'destination': 'null', 'categories': '[]', 'limit': 'null'})
    
    slots_str = ', '.join([f'"{key}":{value}' for key, value in merged_slots.items()])
    return slots_str


def _build_special_rules(analysis):
    """Build special handling rules based on analysis."""
    rules = []
    
    if analysis.get('is_ambiguous'):
        rules.append('7. AMBIGUITY DETECTED: If the user asks for general recommendations without specifying a category, set intent to "ask_clarify" and provide a clarification question.')
    
    if 'multi_intent' in analysis.get('special_handling', []):
        rules.append('8. MULTI-INTENT: This query contains multiple requests. Include all intents in the "intents" array.')
    
    if 'vague_location' in analysis.get('special_handling', []):
        rules.append('9. VAGUE LOCATION: The user mentioned their current location. Set destination to "current_location".')
    
    if analysis.get('context_dependency'):
        rules.append('10. CONTEXT DEPENDENT: Reference the recent conversation context to understand this query.')
    
    return '\n'.join(rules) if rules else ''



def _build_examples_from_analysis(analysis):
    """Build relevant examples based on analysis."""
    from .prompt_config import FEW_SHOT_EXAMPLES
    
    examples = []
    suggested = analysis.get('suggested_examples', [])
    
    # Map query types to example domains
    query_type = analysis.get('query_type', '')
    
    if 'clarification' in query_type or analysis.get('is_ambiguous'):
        examples.extend(FEW_SHOT_EXAMPLES.get('clarification', [])[:1])
    elif 'accommodation' in query_type:
        examples.extend(FEW_SHOT_EXAMPLES.get('accommodation', [])[:1])
    elif 'transport' in query_type or 'flight' in query_type:
        examples.extend(FEW_SHOT_EXAMPLES.get('transport', [])[:1])
    elif 'itinerary' in query_type or 'trip' in query_type:
        examples.extend(FEW_SHOT_EXAMPLES.get('itinerary', [])[:1])
    
    if not examples:
        examples.extend(FEW_SHOT_EXAMPLES.get('general', [])[:1])
    
    if not examples:
        return ""
    
    examples_text = "\n\nRELEVANT EXAMPLES:\n"
    for ex in examples[:2]:  # Max 2 examples
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
            "temperature": 0.7,
            "maxOutputTokens": 200
        }
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
    Main orchestrator function implementing Two-Pass workflow.
    
    ACCURACY FIRST POLICY:
    - Pass 1: Analyze query context dynamically
    - Pass 2: Generate precise response based on analysis
    
    Parameters:
        user_input (str): User's query
        conversation_history (list): Recent conversation messages
    
    Returns:
        dict: Extracted information with maximum accuracy
    """
    
    if not user_input or not user_input.strip():
        return {
            'intents': [],
            'followup': True,
            'clarify_question': 'Please provide more information about your travel plans.'
        }
    
    # PASS 1: ANALYSIS
    print("🔍 Pass 1: Analyzing query...")
    analysis = pass1_analyze_query(user_input, collected_information, conversation_history)
    # print the dictionary analysis
    print("Analysis Result:")
    print(json.dumps(analysis, indent=2))
    print("✅ Analysis complete\n")
    
    # PASS 2: EXECUTION
    print("⚙️  Pass 2: Generating precise response...")
    result = pass2_generate_response(user_input, analysis, collected_information, conversation_history)
    print("✅ Extraction complete\n")
    #print the result
    print("Extraction Result:")
    print(json.dumps(result, indent=2))
    
    return result


# Example usage
if __name__ == "__main__":
    print("=== Two-Pass Orchestrator Testing (ACCURACY FIRST) ===\n")
    
    test_cases = [
        "Tôi muốn tham gia buổi hoà nhạc?",
        "Lên kế hoạch đi vòng quanh hồ gươm và thưởng thức ẩm thực đường phố trong một ngày.",
        "Đi vòng quanh thành phố Hồ Chí Minh, lai rai mấy quán cà phê đẹp và các điểm tham quan lịch sử.",
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        srcLanguage = detectLanguage(test_input)
        test_input = translate(test_input, target_language='en')
        print(f"Test {i}: {test_input}")
        result = extract_info_with_orchestrator(test_input)
        # translate the location names back to Vietnamese for display
        if 'intents' in result:
            for intent in result['intents']:
                if 'slots' in intent and 'destination' in intent['slots'] and intent['slots']['destination']:
                    intent['slots']['destination'] = translate(intent['slots']['destination'], target_language=srcLanguage)
        print(json.dumps(result, indent=2))
        print("\n" + "="*70 + "\n")
