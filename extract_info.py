"""
Extract Info Module
Extracts journey planning information from natural language using Gemini API.
"""

import json
import requests
from datetime import datetime, timedelta

# ============================================================================
# API KEY
# ============================================================================
GEMINI_KEY = 'AIzaSyD-EFl-4leMJZdYItikL2s2N7Ebg3rKhRQ'

def extract_info(text):
    """
    Extract journey planning information from natural language using Gemini API.
    
    Args:
        text: Natural language description of journey plan
        
    Returns:
        dict with keys:
            - must_go_destinations: list of dicts with 'name' and 'order' (first one with order=0 is start)
            - must_go_categories: list of dicts with 'category' and 'order'
            - journey_sequence: ordered list of all stops (destinations and categories mixed)
            - number_of_destinations: int (total number of destinations to visit, default 4)
            - journey_date: str (date in YYYY-MM-DD format, default today)
            - start_time: str (time in HH:MM format, default 2 hours from now)
    """
    if not text or not text.strip():
        # Default values
        default_date = datetime.now().strftime('%Y-%m-%d')
        default_time = (datetime.now() + timedelta(hours=2)).strftime('%H:%M')
        
        return {
            'must_go_destinations': [],
            'must_go_categories': [],
            'journey_sequence': [],
            'number_of_destinations': 4,
            'journey_date': default_date,
            'start_time': default_time
        }
    
    try:
        # Get current date and time for defaults
        current_date = datetime.now().strftime('%Y-%m-%d')
        default_time = (datetime.now() + timedelta(hours=2)).strftime('%H:%M')
        
        # Prepare the prompt for Gemini (minimized whitespace to reduce tokens)
        prompt = f"""Extract journey info from: "{text}"
Return ONLY valid JSON (no markdown):
{{"must_go_destinations":[{{"name":"starting point","order":0}}],"must_go_categories":[{{"category":"restaurant","order":1,"count":1}}],"journey_sequence":[{{"type":"destination","value":"starting point","order":0}},{{"type":"category","value":"restaurant","order":1}}],"number_of_destinations":4,"journey_date":"2025-11-20","start_time":"09:00"}}
Rules: First destination (order:0) is starting location, if not written , set University of Science to be default of starting location. If quantity specified (e.g. "3 museums"), add "count" field and repeat in journey_sequence. Extract journey_date from phrases like "tomorrow", "Monday", "next Friday", "on 2025-12-25" (use YYYY-MM-DD format, default "{current_date}" if not mentioned). Extract start_time from phrases like "7am", "at 9:30", "starting 14:00" (use HH:MM 24-hour format, default "{default_time}" if not mentioned). Normalize categories: restaurant,cafe,museum,park,beach,shopping_mall,market,temple,church,bar,hotel,spa,landmark,etc. Preserve exact order. Default number_of_destinations=4 if not specified."""

        # Call Gemini API
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
        
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract the generated text
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                
                # Check for finish reason issues
                finish_reason = candidate.get('finishReason', '')
                if finish_reason == 'MAX_TOKENS':
                    print("Warning: Response was truncated due to MAX_TOKENS")
                
                if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                    generated_text = candidate['content']['parts'][0].get('text', '')
                    
                    if not generated_text:
                        print(f"No text in response. Finish reason: {finish_reason}")
                        raise ValueError("Empty response from Gemini")
                    
                    # Clean up the response (remove markdown code blocks if present)
                    generated_text = generated_text.strip()
                    if generated_text.startswith('```json'):
                        generated_text = generated_text[7:]
                    if generated_text.startswith('```'):
                        generated_text = generated_text[3:]
                    if generated_text.endswith('```'):
                        generated_text = generated_text[:-3]
                    generated_text = generated_text.strip()
                    
                    # Parse JSON
                    extracted_info = json.loads(generated_text)
                    
                    # Validate and fill missing fields
                    if not extracted_info.get('must_go_destinations'):
                        extracted_info['must_go_destinations'] = []
                    
                    if not extracted_info.get('must_go_categories'):
                        extracted_info['must_go_categories'] = []
                    
                    if not extracted_info.get('number_of_destinations'):
                        extracted_info['number_of_destinations'] = 4
                    
                    if not extracted_info.get('journey_date'):
                        extracted_info['journey_date'] = current_date
                    
                    if not extracted_info.get('start_time'):
                        extracted_info['start_time'] = default_time
                    
                    if not extracted_info.get('journey_sequence'):
                        # Build sequence from individual lists if not provided
                        sequence = []
                        for dest in extracted_info.get('must_go_destinations', []):
                            if isinstance(dest, dict):
                                sequence.append({
                                    'type': 'destination',
                                    'value': dest.get('name', dest),
                                    'order': dest.get('order', len(sequence) + 1)
                                })
                        for cat in extracted_info.get('must_go_categories', []):
                            if isinstance(cat, dict):
                                sequence.append({
                                    'type': 'category',
                                    'value': cat.get('category', cat),
                                    'order': cat.get('order', len(sequence) + 1)
                                })
                        sequence.sort(key=lambda x: x.get('order', 999))
                        extracted_info['journey_sequence'] = sequence
                    
                    return extracted_info
                else:
                    print(f"No parts in content. Candidate: {candidate}")
                    raise ValueError("Invalid response structure from Gemini")
            
            print(f"Unexpected Gemini response structure: {result}")
            
        else:
            print(f"Gemini API error {response.status_code}: {response.text}")
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        if 'generated_text' in locals():
            print(f"Generated text was: {generated_text}")
    except Exception as e:
        print(f"Error extracting info with Gemini: {e}")
    
    # Fallback: return default structure
    default_date = datetime.now().strftime('%Y-%m-%d')
    default_time = (datetime.now() + timedelta(hours=2)).strftime('%H:%M')
    
    return {
        'must_go_destinations': [],
        'must_go_categories': [],
        'journey_sequence': [],
        'number_of_destinations': 4,
        'journey_date': default_date,
        'start_time': default_time
    }


# ============================================================================
# TEST SECTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("EXTRACT INFO MODULE - TESTING")
    print("=" * 80)
    
    # Test cases
    test_cases = [
        "I want to start from HCMUS then have a cafe and then restaurant, visit a park and then go to ben thanh market before going back to HCMUS",
        "Start at Saigon Railway Station tomorrow at 7am, visit 3 museums, have lunch at a local restaurant, then go shopping",
        "Begin from District 1 on Monday at 9:30, check out 2 bars, grab some street food, and end at a spa",
        "From Times Square next Friday at 14:00 visit Statue of Liberty then Central Park then have dinner at a fine dining restaurant"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST CASE {i}")
        print("=" * 80)
        print(f"\n📍 User Request:")
        print(f"   {test_text}")
        print("\n" + "-" * 80)
        
        result = extract_info(test_text)
        
        print(f"\n🎯 Number of Destinations: {result.get('number_of_destinations', 'N/A')}")
        print(f"📅 Journey Date: {result.get('journey_date', 'N/A')}")
        print(f"🕐 Start Time: {result.get('start_time', 'N/A')}")
        
        print("\n📌 Must-Go Destinations:")
        destinations = result.get('must_go_destinations', [])
        if destinations:
            for dest in destinations:
                if isinstance(dest, dict):
                    order = dest.get('order', '?')
                    name = dest.get('name', 'Unknown')
                    if order == 0:
                        print(f"   🏁 {name} (Order: {order} - START)")
                    else:
                        print(f"   • {name} (Order: {order})")
                else:
                    print(f"   • {dest}")
        else:
            print("   (None specified)")
        
        print("\n🏪 Must-Go Categories:")
        categories = result.get('must_go_categories', [])
        if categories:
            for cat in categories:
                if isinstance(cat, dict):
                    count = cat.get('count', 1)
                    category_name = cat.get('category', 'Unknown')
                    order = cat.get('order', '?')
                    if count > 1:
                        print(f"   • {category_name} (Order: {order}, Count: {count})")
                    else:
                        print(f"   • {category_name} (Order: {order})")
                else:
                    print(f"   • {cat}")
        else:
            print("   (None specified)")
        
        print("\n🗺️  Journey Sequence:")
        sequence = result.get('journey_sequence', [])
        if sequence:
            for item in sequence:
                order = item.get('order', '?')
                item_type = item.get('type', 'unknown')
                value = item.get('value', 'Unknown')
                icon = "📍" if item_type == "destination" else "🏪"
                print(f"   {order}. {icon} {value} ({item_type})")
        else:
            print("   (No sequence available)")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
