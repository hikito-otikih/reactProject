"""
Path Constructor Module
Constructs optimal journey path from candidate destinations.
"""

import json
import requests
from datetime import datetime, timedelta
import math

# ============================================================================
# API KEY
# ============================================================================
GEOAPIFY_API_KEY = '3600fc44d95e4e578b698c35f3edbb7d'

# ============================================================================
# CONSTANTS - Estimated visit duration by category (in minutes)
# ============================================================================
CATEGORY_VISIT_DURATION = {
    # Food & Dining
    'restaurant': 60,
    'cafe': 30,
    'catering': 45,
    'bakery': 20,
    'bar': 45,
    'fast_food': 25,
    'food_court': 40,
    'street_food': 20,
    'buffet': 75,
    'fine_dining': 90,
    
    # Tourism & Attractions
    'tourism': 60,
    'landmark': 45,
    'museum': 90,
    'art_gallery': 60,
    'historical_site': 75,
    'monument': 30,
    'cultural_center': 60,
    'temple': 40,
    'church': 30,
    'pagoda': 35,
    'viewpoint': 25,
    'observation_deck': 40,
    'tourist_attraction': 60,
    'theme_park': 180,
    'amusement_park': 180,
    'zoo': 120,
    'aquarium': 90,
    
    # Shopping
    'shopping_mall': 90,
    'shopping_center': 75,
    'market': 60,
    'night_market': 75,
    'souvenir_shop': 30,
    'boutique': 40,
    'department_store': 60,
    'local_market': 50,
    
    # Nature & Outdoors
    'park': 60,
    'garden': 50,
    'beach': 120,
    'lake': 60,
    'mountain': 180,
    'nature_reserve': 90,
    'botanical_garden': 75,
    'waterfall': 45,
    'hiking_trail': 120,
    'national_park': 180,
    
    # Entertainment & Recreation
    'entertainment': 60,
    'theater': 120,
    'cinema': 150,
    'concert_hall': 120,
    'nightclub': 90,
    'karaoke': 90,
    'spa': 90,
    'massage': 60,
    'wellness_center': 75,
    'gym': 60,
    'sports_center': 90,
    
    # Accommodation
    'hotel': 15,
    'hostel': 15,
    'resort': 30,
    'guesthouse': 15,
    
    # Services & Facilities
    'commercial': 30,
    'hospital': 45,
    'pharmacy': 15,
    'bank': 20,
    'atm': 10,
    'post_office': 20,
    'visitor_center': 30,
    'tourist_info': 20,
    
    # Transportation
    'airport': 30,
    'train_station': 20,
    'bus_station': 15,
    'ferry_terminal': 20,
    'taxi_stand': 5,
    
    # Default
    'default': 45
}


def get_visit_duration(category):
    """Get estimated visit duration for a category in minutes"""
    return CATEGORY_VISIT_DURATION.get(category, CATEGORY_VISIT_DURATION['default'])


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    R = 6371  # Earth's radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance


def get_travel_time_geoapify(from_lat, from_lon, to_lat, to_lon):
    """
    Get actual travel time between two points using Geoapify Routing API
    
    Returns:
        dict with 'duration_minutes' and 'distance_km'
    """
    try:
        waypoints = f"{from_lat},{from_lon}|{to_lat},{to_lon}"
        url = f"https://api.geoapify.com/v1/routing?waypoints={waypoints}&mode=drive&apiKey={GEOAPIFY_API_KEY}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                properties = data['features'][0].get('properties', {})
                
                duration_s = properties.get('time', 0)
                duration_min = duration_s / 60.0
                
                distance_m = properties.get('distance', 0)
                distance_km = distance_m / 1000.0
                
                return {
                    'duration_minutes': round(duration_min, 1),
                    'distance_km': round(distance_km, 2)
                }
        
        # Fallback to haversine estimate
        distance = haversine_distance(from_lat, from_lon, to_lat, to_lon)
        estimated_time = distance / 30 * 60  # Assume 30 km/h average speed
        
        return {
            'duration_minutes': round(estimated_time, 1),
            'distance_km': round(distance, 2)
        }
        
    except Exception as e:
        print(f"Geoapify routing error: {e}")
        # Fallback to haversine
        distance = haversine_distance(from_lat, from_lon, to_lat, to_lon)
        estimated_time = distance / 30 * 60
        
        return {
            'duration_minutes': round(estimated_time, 1),
            'distance_km': round(distance, 2)
        }


def is_open_at_time(operating_hours, check_datetime):
    """
    Check if a place is open at a specific datetime
    
    Args:
        operating_hours: dict or None (e.g., {'monday': '9 AM - 5 PM', ...})
        check_datetime: datetime object
        
    Returns:
        bool: True if open or unknown, False if closed
    """
    if not operating_hours or operating_hours == 'N/A':
        return True  # Assume open if no data
    
    try:
        day_name = check_datetime.strftime('%A').lower()
        
        if isinstance(operating_hours, dict):
            hours_str = operating_hours.get(day_name, '')
        else:
            return True
        
        if not hours_str or hours_str.lower() == 'closed':
            return False
        if 'open 24 hours' in hours_str.lower() or '24/7' in hours_str.lower():
            return True
        
        # For now, return True if we have hours (proper parsing would be complex)
        return True
        
    except Exception:
        return True  # Default to open if error


def calculate_score(candidate, current_lat, current_lon):
    """
    Calculate score for a candidate based on rating and distance
    Higher score = better candidate
    
    Score = rating / distance (with minimum distance to avoid division issues)
    """
    rating = float(candidate.get('rating', 0) or 0)
    lat = candidate.get('lat')
    lon = candidate.get('lon')
    
    if not lat or not lon or rating == 0:
        return 0
    
    distance = haversine_distance(current_lat, current_lon, lat, lon)
    # Avoid division by very small numbers
    distance = max(distance, 0.1)
    
    score = rating / distance
    return score


def construct_path(candidate_graph, extracted_info):
    """
    Construct optimal journey path from candidate graph
    
    Args:
        candidate_graph: Output from build_candidate_graph
        extracted_info: Output from extract_info
        
    Returns:
        dict with:
            - path: list of selected destinations with visit times
            - total_duration_minutes: total journey time
            - total_distance_km: total distance
    """
    # Parse start date and time
    journey_date_str = extracted_info.get('journey_date')
    start_time_str = extracted_info.get('start_time')
    
    try:
        current_time = datetime.strptime(f"{journey_date_str} {start_time_str}", "%Y-%m-%d %H:%M")
    except:
        current_time = datetime.now() + timedelta(hours=2)
    
    # Initialize path with starting location
    anchor_locations = candidate_graph.get('anchor_locations', [])
    if not anchor_locations:
        return {'path': [], 'total_duration_minutes': 0, 'total_distance_km': 0}
    
    # Sort anchor locations by order
    anchor_locations.sort(key=lambda x: x.get('order', 999))
    start_location = anchor_locations[0]
    
    path = [{
        'order': 0,
        'name': start_location['name'],
        'type': 'start',
        'category': 'start',
        'lat': start_location['lat'],
        'lon': start_location['lon'],
        'arrival_time': current_time.strftime('%Y-%m-%d %H:%M'),
        'departure_time': current_time.strftime('%Y-%m-%d %H:%M'),
        'visit_duration_minutes': 0,
        'travel_from_previous_minutes': 0,
        'distance_from_previous_km': 0
    }]
    
    current_lat = start_location['lat']
    current_lon = start_location['lon']
    
    # Get journey sequence from extracted_info
    journey_sequence = extracted_info.get('journey_sequence', [])
    category_candidates = candidate_graph.get('category_candidates', {})
    
    # Process each item in journey sequence
    for seq_item in journey_sequence:
        item_type = seq_item.get('type')
        value = seq_item.get('value')
        order = seq_item.get('order')
        
        if order == 0:  # Skip start location
            continue
        
        if item_type == 'destination':
            # Find the destination in anchor_locations
            dest = next((loc for loc in anchor_locations if loc['name'].lower() == value.lower()), None)
            if dest:
                # Calculate travel time
                travel_info = get_travel_time_geoapify(current_lat, current_lon, dest['lat'], dest['lon'])
                
                # Update current time with travel
                current_time += timedelta(minutes=travel_info['duration_minutes'])
                arrival_time = current_time
                
                # Visit duration (minimal for must-go destinations)
                visit_duration = 30
                current_time += timedelta(minutes=visit_duration)
                
                path.append({
                    'order': order,
                    'name': dest['name'],
                    'type': 'destination',
                    'category': 'destination',
                    'lat': dest['lat'],
                    'lon': dest['lon'],
                    'arrival_time': arrival_time.strftime('%Y-%m-%d %H:%M'),
                    'departure_time': current_time.strftime('%Y-%m-%d %H:%M'),
                    'visit_duration_minutes': visit_duration,
                    'travel_from_previous_minutes': travel_info['duration_minutes'],
                    'distance_from_previous_km': travel_info['distance_km']
                })
                
                current_lat = dest['lat']
                current_lon = dest['lon']
        
        elif item_type == 'category':
            # Select best candidate from this category
            category_data = category_candidates.get(value, {})
            candidates = category_data.get('candidates', [])
            
            if not candidates:
                continue
            
            # Score all candidates and filter by operating hours
            scored_candidates = []
            for candidate in candidates:
                # Check if open
                if not is_open_at_time(candidate.get('operating_hours'), current_time):
                    continue
                
                score = calculate_score(candidate, current_lat, current_lon)
                if score > 0:
                    scored_candidates.append({
                        'candidate': candidate,
                        'score': score
                    })
            
            if not scored_candidates:
                # If none are open, take best rated regardless
                scored_candidates = [
                    {'candidate': c, 'score': calculate_score(c, current_lat, current_lon)}
                    for c in candidates if calculate_score(c, current_lat, current_lon) > 0
                ]
            
            if scored_candidates:
                # Select best candidate
                scored_candidates.sort(key=lambda x: x['score'], reverse=True)
                selected = scored_candidates[0]['candidate']
                
                # Calculate travel time
                travel_info = get_travel_time_geoapify(current_lat, current_lon, selected['lat'], selected['lon'])
                
                # Update current time with travel
                current_time += timedelta(minutes=travel_info['duration_minutes'])
                arrival_time = current_time
                
                # Visit duration based on category
                visit_duration = get_visit_duration(value)
                current_time += timedelta(minutes=visit_duration)
                
                path.append({
                    'order': order,
                    'name': selected['name'],
                    'type': 'category',
                    'category': value,
                    'lat': selected['lat'],
                    'lon': selected['lon'],
                    'rating': selected.get('rating'),
                    'reviews': selected.get('reviews'),
                    'address': selected.get('address'),
                    'arrival_time': arrival_time.strftime('%Y-%m-%d %H:%M'),
                    'departure_time': current_time.strftime('%Y-%m-%d %H:%M'),
                    'visit_duration_minutes': visit_duration,
                    'travel_from_previous_minutes': travel_info['duration_minutes'],
                    'distance_from_previous_km': travel_info['distance_km']
                })
                
                current_lat = selected['lat']
                current_lon = selected['lon']
    
    # Calculate totals
    total_duration = sum(stop['visit_duration_minutes'] + stop['travel_from_previous_minutes'] for stop in path)
    total_distance = sum(stop['distance_from_previous_km'] for stop in path)
    
    return {
        'path': path,
        'total_duration_minutes': round(total_duration, 1),
        'total_distance_km': round(total_distance, 2),
        'start_time': path[0]['arrival_time'],
        'end_time': path[-1]['departure_time']
    }


# ============================================================================
# TEST SECTION
# ============================================================================

if __name__ == "__main__":
    from extract_info import extract_info
    from candidate_graph import build_candidate_graph
    
    print("=" * 80)
    print("PATH CONSTRUCTOR - TESTING")
    print("=" * 80)
    
    # Test case
    test_text = "I want to start from Landmark 81 tomorrow at 9am, visit a spa, have lunch at a restaurant, then go to Ben Thanh Market"
    
    print(f"\n📍 User Request:")
    print(f"   {test_text}")
    print("\n" + "=" * 80)
    
    # Step 1: Extract info
    print("STEP 1: Extracting information...")
    extracted_info = extract_info(test_text)
    print(f"✓ Journey Date: {extracted_info.get('journey_date')}")
    print(f"✓ Start Time: {extracted_info.get('start_time')}")
    
    # Step 2: Build candidate graph
    print("\nSTEP 2: Building candidate graph...")
    candidate_graph = build_candidate_graph(extracted_info)
    print(f"✓ Anchor locations: {len(candidate_graph['anchor_locations'])}")
    print(f"✓ Categories: {list(candidate_graph['category_candidates'].keys())}")
    
    # Step 3: Construct path
    print("\nSTEP 3: Constructing optimal path...")
    path_result = construct_path(candidate_graph, extracted_info)
    
    print("\n" + "=" * 80)
    print("CONSTRUCTED PATH")
    print("=" * 80)
    
    print(f"\n🕐 Journey Time: {path_result['start_time']} → {path_result['end_time']}")
    print(f"⏱️  Total Duration: {path_result['total_duration_minutes']} minutes ({path_result['total_duration_minutes']/60:.1f} hours)")
    print(f"📏 Total Distance: {path_result['total_distance_km']} km")
    
    print(f"\n🗺️  PATH ({len(path_result['path'])} stops):")
    for stop in path_result['path']:
        print(f"\n   {stop['order']}. {stop['name']}")
        print(f"      📍 Category: {stop['category']}")
        if stop.get('rating'):
            print(f"      ⭐ Rating: {stop['rating']} ({stop.get('reviews', 'N/A')} reviews)")
        print(f"      🕐 Arrival: {stop['arrival_time']}")
        print(f"      🕑 Departure: {stop['departure_time']}")
        print(f"      ⏱️  Visit Duration: {stop['visit_duration_minutes']} min")
        if stop['travel_from_previous_minutes'] > 0:
            print(f"      🚗 Travel from previous: {stop['travel_from_previous_minutes']} min ({stop['distance_from_previous_km']} km)")
    
    print("\n" + "=" * 80)
    print("JSON OUTPUT:")
    print("=" * 80)
    print(json.dumps(path_result, indent=2, ensure_ascii=False))
    print("=" * 80)
