import json
import math
import requests
from datetime import datetime, timedelta
from functools import lru_cache
import random
from extract_info import extract_info
from candidate_graph import build_candidate_graph
from path_constructor import construct_path

# ============================================================================
# API KEYS
# ============================================================================
GEOAPIFY_API_KEY = '3600fc44d95e4e578b698c35f3edbb7d'
# ============================================================================
# CONSTANTS
# ============================================================================
AVAILABLE_CATEGORIES = [
    # Food & Dining
    'restaurant', 'cafe', 'catering', 'bakery', 'bar', 'fast_food', 'food_court',
    'street_food', 'buffet', 'fine_dining',
    
    # Tourism & Attractions
    'tourism', 'landmark', 'museum', 'art_gallery', 'historical_site', 'monument',
    'cultural_center', 'temple', 'church', 'pagoda', 'viewpoint', 'observation_deck',
    'tourist_attraction', 'theme_park', 'amusement_park', 'zoo', 'aquarium',
    
    # Shopping
    'shopping_mall', 'shopping_center', 'market', 'night_market', 'souvenir_shop',
    'boutique', 'department_store', 'local_market',
    
    # Nature & Outdoors
    'park', 'garden', 'beach', 'lake', 'mountain', 'nature_reserve', 'botanical_garden',
    'waterfall', 'hiking_trail', 'national_park',
    
    # Entertainment & Recreation
    'entertainment', 'theater', 'cinema', 'concert_hall', 'nightclub', 'karaoke',
    'spa', 'massage', 'wellness_center', 'gym', 'sports_center',
    
    # Accommodation
    'hotel', 'hostel', 'resort', 'guesthouse',
    
    # Services & Facilities
    'commercial', 'hospital', 'pharmacy', 'bank', 'atm', 'post_office',
    'visitor_center', 'tourist_info',
    
    # Transportation
    'airport', 'train_station', 'bus_station', 'ferry_terminal', 'taxi_stand'
]

def path(text): 
    print(f"\n📝 Input: {text}")
    
    info = extract_info(text)
    print(f"✓ Extracted: {len(info.get('must_go_destinations', []))} destinations, {len(info.get('must_go_categories', []))} categories")
    
    graph = build_candidate_graph(info)
    print(f"✓ Found: {len(graph['anchor_locations'])} anchors, {sum(len(d['candidates']) for d in graph['category_candidates'].values())} candidates")
    
    optimal_path = construct_path(graph, info)
    print(f"✓ Path: {len(optimal_path['path'])} stops, {optimal_path['total_duration_minutes']//60}h{optimal_path['total_duration_minutes']%60}m, {optimal_path['total_distance_km']:.1f}km")
    
    print(f"\n🗺️  {optimal_path['start_time']} → {optimal_path['end_time']}")
    for i, stop in enumerate(optimal_path['path'], 1):
        travel = f" +{stop['travel_time_minutes']}m" if stop.get('travel_time_minutes') else ""
        print(f"   {i}. {stop['name']} ({stop['visit_duration_minutes']}m{travel})")
    
    return optimal_path
    



if __name__ == "__main__":
    print("=" * 80)
    print("JOURNEY PLANNER - TESTS")
    print("=" * 80)
    
    tests = [
        "A day strip starting from Saigon Notre-Dame Cathedral Basilica then visit Dalat, visit 2 restaurants and a cafe",
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*80}\nTest {i}/{len(tests)}\n{'='*80}")
        result = path(test)
        
        # Print detailed trip information
        print("\n" + "=" * 80)
        print("DETAILED TRIP INFORMATION")
        print("=" * 80)
        
        print(f"\n📅 Journey Date: {result['start_time'].split()[0]}")
        print(f"⏰ Start Time: {result['start_time']}")
        print(f"⏰ End Time: {result['end_time']}")
        print(f"⏱️  Total Duration: {result['total_duration_minutes']} minutes ({result['total_duration_minutes']//60}h {result['total_duration_minutes']%60}m)")
        print(f"🚗 Total Distance: {result['total_distance_km']:.2f} km")
        print(f"📍 Total Stops: {len(result['path'])}")
        
        print(f"\n{'='*80}")
        print("ITINERARY")
        print("=" * 80)
        
        for i, stop in enumerate(result['path'], 1):
            print(f"\n🔹 Stop {i}: {stop['name']}")
            print(f"   Type: {stop['type'].title()}")
            if stop.get('category'):
                print(f"   Category: {stop['category'].replace('_', ' ').title()}")
            print(f"   Location: {stop['lat']:.6f}, {stop['lon']:.6f}")
            if stop.get('address'):
                print(f"   Address: {stop['address']}")
            if stop.get('rating'):
                print(f"   Rating: ⭐ {stop['rating']}")
            print(f"   Arrival: {stop['arrival_time']}")
            print(f"   Departure: {stop['departure_time']}")
            print(f"   Visit Duration: {stop['visit_duration_minutes']} minutes")
            
            if stop.get('travel_time_minutes') and stop['travel_time_minutes'] > 0:
                print(f"\n   → Travel to next stop:")
                print(f"      Time: {stop['travel_time_minutes']} minutes")
                print(f"      Distance: {stop['distance_to_next_km']:.2f} km")
        
        print("\n" + "=" * 80)
    
    print(f"\n{'='*80}\n✅ ALL TESTS COMPLETED\n{'='*80}")
