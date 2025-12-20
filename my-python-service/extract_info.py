"""
Extract Info Module
Extracts journey planning information from natural language using Gemini API.
"""

import json
import requests
import math
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
load_dotenv()

# ============================================================================
# API KEY
# ============================================================================
GEMINI_KEY = os.getenv('GEMINI_KEY')
GEOAPIFY_API_KEY = os.getenv('GEOAPIFY_API_KEY')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def geocode_location(location_name):
    """Convert location name to coordinates using OpenStreetMap Nominatim API with Geoapify fallback"""
    if not location_name:
        return None
        
    # 1. Try OpenStreetMap Nominatim first
    try:
        # Nominatim requires a User-Agent header
        headers = {
            'User-Agent': 'JourneyPlannerApp/1.0'
        }
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'q': location_name + ", Viet Nam", 
                'format': 'json', 
                'limit': 1
            },
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data:
                # Nominatim returns lat/lon as strings, convert to float
                return {'lat': float(data[0]['lat']), 'lon': float(data[0]['lon'])}
    except Exception as e:
        print(f"OSM Geocoding error: {e}")
        
    # 2. Fallback to Geoapify if OSM fails or returns no results
    try:
        response = requests.get(
            'https://api.geoapify.com/v1/geocode/search',
            params={
                'text': location_name, 
                'apiKey': GEOAPIFY_API_KEY,
                'filter': 'countrycode:vn'
            },
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('features'):
                coords = data['features'][0].get('geometry', {}).get('coordinates', [])
                if len(coords) >= 2:
                    return {'lat': coords[1], 'lon': coords[0]}
        return None
    except Exception as e:
        print(f"Geoapify Geocoding error: {e}")
        return None

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    R = 6371  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def _default_start_hcmus():
    """Return default starting-location dict for HCMUS."""
    return {'name': 'HCMUS', 'order': 0}

def optimize_journey_sequence(extracted_info):
    # return extracted_info 
    """
    Analyze journey sequence and insert intermediate categories if consecutive 
    destinations are too far apart.
    """
    sequence = extracted_info.get('journey_sequence', [])
    if not sequence or len(sequence) < 2:
        return extracted_info

    new_sequence = []
    must_go_categories = extracted_info.get('must_go_categories', [])
    
    # Cache for geocoding to avoid redundant calls
    location_cache = {}

    for i in range(len(sequence)):
        current_item = sequence[i]
        new_sequence.append(current_item)
        
        # Check if we have a next item
        if i < len(sequence) - 1:
            next_item = sequence[i+1]
            
            # Only check distance between two fixed destinations.
            # If there is a category between them (e.g. Dest A -> Category -> Dest B),
            # they won't be consecutive in this list, so we won't insert anything.
            # This respects the user's specified intermediate stops.
            if current_item.get('type') == 'destination' and next_item.get('type') == 'destination':
                loc1_name = current_item.get('value')
                loc2_name = next_item.get('value')
                
                # Get coordinates
                if loc1_name not in location_cache:
                    location_cache[loc1_name] = geocode_location(loc1_name)
                if loc2_name not in location_cache:
                    location_cache[loc2_name] = geocode_location(loc2_name)
                
                coords1 = location_cache[loc1_name]
                coords2 = location_cache[loc2_name]
                
                if coords1 and coords2:
                    dist = haversine_distance(coords1['lat'], coords1['lon'], coords2['lat'], coords2['lon'])
                    
                    # Logic to insert categories based on distance
                    inserted_categories = []
                    if dist > 10:
                        # Long distance: Insert a major attraction and a food stop
                        # Randomly select to provide variety
                        attractions = ['museum', 'park', 'landmark', 'shopping_mall', 'market', 'temple']
                        food_spots = ['restaurant', 'food_court', 'cafe']
                        
                        inserted_categories = [
                            random.choice(attractions),
                            random.choice(food_spots)
                        ]
                    elif dist > 5:
                        # Medium distance: Insert a quick break
                        quick_stops = ['cafe', 'street_food', 'souvenir_shop', 'park', 'bakery']
                        inserted_categories = [random.choice(quick_stops)]
                    
                    for cat in inserted_categories:
                        # Create new category item
                        new_item = {
                            'type': 'category',
                            'value': cat,
                            'order': 0, # Will re-index later
                            'is_auto_inserted': True
                        }
                        new_sequence.append(new_item)
                        
                        # Update must_go_categories list
                        must_go_categories.append({
                            'category': cat,
                            'order': 0,
                            'count': 1,
                            'is_auto_inserted': True
                        })

    # Re-index orders
    for idx, item in enumerate(new_sequence):
        item['order'] = idx
        
        # Sync order back to must_go_destinations/categories if needed
        if item['type'] == 'destination':
            for d in extracted_info['must_go_destinations']:
                if d.get('name') == item['value']:
                    d['order'] = idx
        elif item['type'] == 'category':
            # This is trickier since there can be multiple of same category
            # We'll just ensure the main list has them
            pass

    extracted_info['journey_sequence'] = new_sequence
    extracted_info['must_go_categories'] = must_go_categories
    
    return extracted_info

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
        
        # Default start
        start = _default_start_hcmus()
        
        return {
            'must_go_destinations': [start],
            'must_go_categories': [],
            'journey_sequence': [{'type': 'destination', 'value': start['name'], 'order': 0}],
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
        {
            {
                "must_go_categories":[{"category":"restaurant","order":1,"count":1}],
                "must_go_destinations":[{"name":"starting point","order":0}],
                "journey_sequence":[{"type":"destination","value":"starting point","order":0},{"type":"category","value":"airport","order":1}],"number_of_destinations":4,"journey_date":"2025-11-20","start_time":"09:00"}}
            Rules: First destination (order:0) is starting location, if user do not specify their starting location set HCMUS to be starting location. If quantity specified (e.g. "3 museums"), add "count" field and repeat in journey_sequence. Extract journey_date from phrases like "tomorrow", "Monday", "next Friday", "on 2025-12-25" (use YYYY-MM-DD format, default "{current_date}" if not mentioned). Extract start_time from phrases like "7am", "at 9:30", "starting 14:00" (use HH:MM 24-hour format, default "{default_time}" if not mentioned). Normalize categories: restaurant,cafe,museum,park,beach,shopping_mall,market,temple,church,bar,hotel,spa,landmark,etc. Preserve exact order. Default number_of_destinations=4 if not specified."""

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
        
        response = requests.post(url, headers=headers, json=data, timeout=40)
        
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
                    
                    # Ensure start location
                    has_start = any(d.get('order') == 0 for d in extracted_info.get('must_go_destinations', []) if isinstance(d, dict))
                    if not has_start:
                        extracted_info['must_go_destinations'].insert(0, _default_start_hcmus())

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
                    else:
                        # Ensure start in sequence
                        has_start_seq = any(item.get('order') == 0 for item in extracted_info.get('journey_sequence', []) if isinstance(item, dict))
                        if not has_start_seq:
                            start = _default_start_hcmus()
                            # Shift orders
                            for item in extracted_info['journey_sequence']:
                                if isinstance(item, dict) and isinstance(item.get('order'), int):
                                    item['order'] += 1
                            extracted_info['journey_sequence'].insert(0, {'type': 'destination', 'value': start['name'], 'order': 0})
                    
                    # Optimize sequence
                    extracted_info = optimize_journey_sequence(extracted_info)
                    
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
    start = _default_start_hcmus()
    
    return {
        'must_go_destinations': [start],
        'must_go_categories': [],
        'journey_sequence': [{'type': 'destination', 'value': start['name'], 'order': 0}],
        'number_of_destinations': 4,
        'journey_date': default_date,
        'start_time': default_time
    }


# ============================================================================
# TEST SECTION
# ============================================================================

if __name__ == "__main__":
    print("EXTRACT INFO MODULE - TESTING")
    print("=" * 80)
    
    # Test cases
    test_cases = [
        "journey to Da Lat",
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