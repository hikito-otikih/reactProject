"""
Candidate Graph Builder Module - UPDATED WITH MIDPOINT SEARCH
"""

import json
import requests
from serpapi import GoogleSearch
from dotenv import load_dotenv
import os
import math

load_dotenv()

SERPAPI_KEY = os.getenv('SERPAPI_KEY')
GEOAPIFY_API_KEY = os.getenv('GEOAPIFY_API_KEY')

def geocode_location(location_name):
    """Convert location name to coordinates using Geoapify"""
    if not location_name: return None
    try:
        response = requests.get(
            'https://api.geoapify.com/v1/geocode/search',
            params={'text': location_name + ", Viet Nam", 'apiKey': GEOAPIFY_API_KEY},
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

def calculate_midpoint(lat1, lon1, lat2, lon2, ratio=0.5):
    """
    Calculate a point between two coordinates.
    ratio: 0.5 is exactly middle. 0.33 is 1/3rd from start, etc.
    """
    new_lat = lat1 + (lat2 - lat1) * ratio
    new_lon = lon1 + (lon2 - lon1) * ratio
    return new_lat, new_lon

def search_candidates(category, location_name, lat, lon, radius_km=10, limit=10):
    """
    Search using SerpAPI with explicit coordinates.
    We don't rely on 'location_name' for the search query if we have coords,
    to prevent Google from snapping back to the city center.
    """
    try:
        # We search for "Category near Lat,Lon" or just "Category" with 'll' parameter
        # Using the coordinate in the query helps Google understand we want that specific area
        query = f"{category}"
        
        # Determine zoom level roughly based on radius. 12-13 is good for inter-district.
        zoom = 13 
        
        params = {
            "api_key": SERPAPI_KEY,
            "engine": "google_maps",
            "type": "search",
            "google_domain": "google.com",
            "q": query,
            "ll": f"@{lat},{lon},{zoom}z", 
            "hl": "en",
            "start": 0,
            "num": limit 
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        candidates = []
        
        # Helper to process a result item
        def process_result(res):
            gps = res.get('gps_coordinates', {})
            return {
                'name': res.get('title'),
                'category': category,
                'rating': res.get('rating'),
                'reviews': res.get('reviews'),
                'address': res.get('address'),
                'lat': gps.get('latitude'),
                'lon': gps.get('longitude'),
                'operating_hours': res.get('operating_hours'),
                'anchor_location': location_name # Metadata for debugging
            }

        if 'place_results' in results:
            candidates.append(process_result(results["place_results"]))
        elif 'local_results' in results:
            for res in results['local_results'][:limit]:
                candidates.append(process_result(res))
                
        return candidates
        
    except Exception as e:
        print(f"SerpAPI search error: {e}")
        return []

def build_candidate_graph(extracted_info):
    # 1. Resolve Anchor Locations (Must-Go)
    anchor_locations = []
    destinations = extracted_info.get('must_go_destinations', [])
    
    # Map to store resolved coordinates: {'Name': {'lat': x, 'lon': y}}
    resolved_coords = {}

    for dest in destinations:
        if isinstance(dest, dict):
            name = dest.get('name')
            coords = geocode_location(name)
            if coords:
                coords['name'] = name
                coords['order'] = dest.get('order', 999)
                anchor_locations.append(coords)
                resolved_coords[name] = coords
    
    anchor_locations.sort(key=lambda x: x['order'])

    if not anchor_locations:
        return {'anchor_locations': [], 'category_candidates': {}}

    # 2. Analyze Sequence to find Search Points
    # We iterate through the sequence to find "Gaps" between anchors
    sequence = extracted_info.get('journey_sequence', [])
    category_candidates = {}
    
    # We need to assign specific search coordinates to each category request
    # List of tasks: [{'category': 'restaurant', 'search_lat': ..., 'search_lon': ...}]
    search_tasks = []

    last_anchor = anchor_locations[0] # Start point
    
    # Filter only destinations that are actually resolved anchors
    seq_anchors_indices = [i for i, x in enumerate(sequence) 
                          if x['type'] == 'destination' and x['value'] in resolved_coords]

    # Iterate through segments (e.g., Start -> ... -> End)
    for i in range(len(seq_anchors_indices) - 1):
        curr_idx = seq_anchors_indices[i]
        next_idx = seq_anchors_indices[i+1]
        
        curr_anchor_name = sequence[curr_idx]['value']
        next_anchor_name = sequence[next_idx]['value']
        
        curr_coords = resolved_coords[curr_anchor_name]
        next_coords = resolved_coords[next_anchor_name]
        
        # Find intermediate items between these two anchors
        intermediate_items = sequence[curr_idx+1 : next_idx]
        categories_in_between = [x for x in intermediate_items if x['type'] == 'category']
        
        count = len(categories_in_between)
        
        if count > 0:
            # We have categories to fill between A and B
            # Distribute them evenly. 
            # If 1 item: at 50%
            # If 2 items: at 33% and 66%
            for k, item in enumerate(categories_in_between, 1):
                ratio = k / (count + 1)
                mid_lat, mid_lon = calculate_midpoint(
                    curr_coords['lat'], curr_coords['lon'],
                    next_coords['lat'], next_coords['lon'],
                    ratio
                )
                
                search_tasks.append({
                    'category': item['value'],
                    'lat': mid_lat,
                    'lon': mid_lon,
                    'ref_name': f"Midpoint {k} between {curr_anchor_name} & {next_anchor_name}"
                })
        
    # Handle "Dangling" categories (if any appear after the last destination)
    # Just search near the last destination
    last_idx = seq_anchors_indices[-1] if seq_anchors_indices else 0
    if last_idx < len(sequence) - 1:
        tail_items = sequence[last_idx+1:]
        last_coords = resolved_coords[sequence[last_idx]['value']]
        for item in tail_items:
            if item['type'] == 'category':
                search_tasks.append({
                    'category': item['value'],
                    'lat': last_coords['lat'],
                    'lon': last_coords['lon'],
                    'ref_name': f"Near {sequence[last_idx]['value']}"
                })

    # 3. Execute Search Tasks
    # Group by category to match your original output structure, 
    # but strictly add candidates based on the calculated geometric points.
    
    for task in search_tasks:
        cat = task['category']
        print(f"Searching for {cat} at {task['ref_name']}...")
        
        candidates = search_candidates(
            cat, task['ref_name'], task['lat'], task['lon'], limit=10
        )
        
        if cat not in category_candidates:
            category_candidates[cat] = {
                'category': cat,
                'required_count': 1, # Simplified logic
                'candidates': []
            }
        
        # Add these candidates to the pool
        # We extend the list. The path_constructor will pick the best one later based on travel time.
        category_candidates[cat]['candidates'].extend(candidates)
        # Update required count
        category_candidates[cat]['required_count'] = len([t for t in search_tasks if t['category'] == cat])

    # Deduplicate candidates
    for cat in category_candidates:
        unique = []
        seen = set()
        for c in category_candidates[cat]['candidates']:
            key = f"{c['name']}_{c.get('lat')}"
            if key not in seen:
                seen.add(key)
                unique.append(c)
        # Sort by rating
        unique.sort(key=lambda x: float(x.get('rating', 0) or 0), reverse=True)
        category_candidates[cat]['candidates'] = unique[:30] # Limit pool size

    return {
        'anchor_locations': anchor_locations,
        'category_candidates': category_candidates
    }