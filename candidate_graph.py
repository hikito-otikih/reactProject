"""
Candidate Graph Builder Module
Builds a graph of possible destination candidates for journey planning.
"""

import json
import requests
from serpapi import GoogleSearch

# ============================================================================
# API KEYS
# ============================================================================
SERPAPI_KEY = 'ed59ce3a8847be0b542c889c1d8722609f71b3ea311ae8ef2a78533574c0359a'
GEOAPIFY_API_KEY = '3600fc44d95e4e578b698c35f3edbb7d'


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def geocode_location(location_name):
    """Convert location name to coordinates using Geoapify"""
    if not location_name:
        return None
    try:
        response = requests.get(
            'https://api.geoapify.com/v1/geocode/search',
            params={'text': location_name + ", VN", 'apiKey': GEOAPIFY_API_KEY},
            timeout=6
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('features'):
                coords = data['features'][0].get('geometry', {}).get('coordinates', [])
                if len(coords) >= 2:
                    return {'lat': coords[1], 'lon': coords[0]}
        return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


def search_candidates_near_location(category, location_name, lat, lon, limit=10):
    """
    Search for places of a specific category near a location using SerpAPI.
    
    Args:
        category: Category type (e.g., 'spa', 'restaurant', 'museum')
        location_name: Name of the anchor location
        lat: Latitude of the anchor location
        lon: Longitude of the anchor location
        limit: Maximum number of results to return
        
    Returns:
        List of candidate places with details
    """
    try:
        params = {
            "api_key": SERPAPI_KEY,
            "engine": "google_maps",
             "google_domain": "google.com",
            "q": f"{category} near {location_name}",
            "ll": f"@{10.763056931422451},{106.68255749755662},14z",
            "type": "search",
            "hl": "en"
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        candidates = []
        if 'place_results' in results:
            place_results = results["place_results"]
            gps = place_results.get('gps_coordinates', {})
            candidates.append({
                'name': place_results['title'],
                'category': category,
                'rating': place_results['rating'],
                'reviews': place_results['reviews'],
                'address': place_results['address'],
                'lat': place_results['gps_coordinates']['latitude'],
                'lon': place_results['gps_coordinates']['longitude'],
                'operating_hours': {
                                "sunday":
                                "0 AM–24 PM",
                                "monday":
                                "0 AM–24 PM",
                                "tuesday":
                                "0 AM–24 PM",
                                "wednesday":
                                "0 AM–24 PM",
                                "thursday":
                                "0 AM–24 PM",
                                "friday":
                                "0 AM–24 PM",
                                "saturday":
                                "0 AM–24 PM"
                                    },
                'anchor_location': location_name
            })
        else:
            local_results = results.get("local_results", [])
            for res in local_results[:limit]:
                gps = res.get('gps_coordinates', {})
                candidates.append({
                    'name': res.get('title'),
                    'category': category,
                    'rating': res.get('rating'),
                    'reviews': res.get('reviews'),
                    'address': res.get('address'),
                    'lat': gps.get('latitude'),
                    'lon': gps.get('longitude'),
                    'operating_hours': res.get('operating_hours'),
                    'anchor_location': location_name
                })
        return candidates
        
    except Exception as e:
        print(f"SerpAPI search error for {category} near {location_name}: {e}")
        return []


def build_candidate_graph(extracted_info):
    """
    Build a graph of candidate locations for each category based on extracted journey info.
    
    Args:
        extracted_info: Output from extract_info function
        
    Returns:
        dict with structure:
        {
            'anchor_locations': [list of reference points with coordinates],
            'category_candidates': {
                'category_name': {
                    'category': str,
                    'required_count': int,
                    'candidates': [list of candidate places]
                },
                ...
            }
        }
    """
    # Get anchor locations (start + must-go destinations)
    anchor_locations = []
    destinations = extracted_info.get('must_go_destinations', [])
    
    for dest in destinations:
        if isinstance(dest, dict):
            name = dest.get('name')
            coords = geocode_location(name)
            if coords:
                anchor_locations.append({
                    'name': name,
                    'lat': coords['lat'],
                    'lon': coords['lon'],
                    'order': dest.get('order', 999)
                })
    
    if not anchor_locations:
        print("No anchor locations found")
        return {'anchor_locations': [], 'category_candidates': {}}
    
    # Build candidates for each category
    category_candidates = {}
    categories = extracted_info.get('must_go_categories', [])
    
    for cat_info in categories:
        if isinstance(cat_info, dict):
            category = cat_info.get('category')
            count = cat_info.get('count', 1)
            
            if not category:
                continue
            
            # Search near each anchor location
            all_candidates = []
            for anchor in anchor_locations:
                candidates = search_candidates_near_location(
                    category=category,
                    location_name=anchor['name'],
                    lat=anchor['lat'],
                    lon=anchor['lon'],
                    limit=10
                )
                all_candidates.extend(candidates)
            
            # Deduplicate by name and location
            unique_candidates = []
            seen = set()
            for candidate in all_candidates:
                key = f"{candidate['name']}_{candidate.get('lat', '')}_{candidate.get('lon', '')}"
                if key not in seen and candidate.get('lat') and candidate.get('lon'):
                    seen.add(key)
                    unique_candidates.append(candidate)
            
            # Sort by rating
            unique_candidates.sort(key=lambda x: float(x.get('rating', 0) or 0), reverse=True)
            
            category_candidates[category] = {
                'category': category,
                'required_count': count,
                'candidates': unique_candidates[:20]  # Keep top 20
            }
    
    return {
        'anchor_locations': anchor_locations,
        'category_candidates': category_candidates
    }


# ============================================================================
# TEST SECTION
# ============================================================================

if __name__ == "__main__":
    from extract_info import extract_info
    
    print("=" * 80)
    print("CANDIDATE GRAPH BUILDER - TESTING")
    print("=" * 80)
    
    # Test cases
    test_cases = [
        "go to airport"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST CASE {i}")
        print("=" * 80)
        print(f"\n📍 User Request:")
        print(f"   {test_text}")
        print("\n" + "-" * 80)
        
        # Extract info
        extracted_info = extract_info(test_text)
        
        # Build candidate graph
        graph = build_candidate_graph(extracted_info)
        
        print(f"\n📍 Anchor Locations Found: {len(graph['anchor_locations'])}")
        for anchor in graph['anchor_locations']:
            print(f"   • {anchor['name']} (Order: {anchor['order']}) - Lat: {anchor['lat']:.4f}, Lon: {anchor['lon']:.4f}")
        
        print(f"\n🏪 Category Candidates:")
        for category, data in graph['category_candidates'].items():
            count = data['required_count']
            num_candidates = len(data['candidates'])
            print(f"\n   📦 {category.upper()} (Need: {count}, Found: {num_candidates} candidates)")
            for j, candidate in enumerate(data['candidates'][:3], 1):  # Show top 3
                rating = candidate.get('rating', 'N/A')
                reviews = candidate.get('reviews', 'N/A')
                print(f"      {j}. {candidate['name']}")
                print(f"         Rating: {rating} ({reviews} reviews) - Near: {candidate['anchor_location']}")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
