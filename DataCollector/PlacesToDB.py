import requests
import pandas as pd
import sqlite3
import json
import os
from dotenv import load_dotenv
from db_utils import search_by_name

load_dotenv()
GEOAPIFY_KEY = os.getenv('GEOAPIFY_KEY')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(SCRIPT_DIR, 'result')
CATEGORIES = ["accommodation", "activity", "catering",
        "commercial", "entertainment",
        "heritage", "leisure",
        "manufacturing", "natural",
        "religion", "rental", 
        "service", "tourism"]

# Create result directory if it doesn't exist
os.makedirs(RESULT_DIR, exist_ok=True)

def get_coordinates(address):
    url = f"https://api.geoapify.com/v1/geocode/search?text={address}&format=json&apiKey={GEOAPIFY_KEY}"
    data = requests.get(url).json()
    if data['results']:
        return data['results'][0]['lon'], data['results'][0]['lat']
    raise ValueError("Address not found")

def fetch_places(address, radius, limit):
    """Fetch places from API and combine into single structure"""
    lon, lat = get_coordinates(address)
    all_locations = []
    place_id = 0
    
    for category in CATEGORIES:
        url = f"https://api.geoapify.com/v2/places?categories={category}&filter=circle:{lon},{lat},{radius}&bias=proximity:{lon},{lat}&limit={limit}&apiKey={GEOAPIFY_KEY}"
        data = requests.get(url).json()
        
        for place in data.get('features', []):
            place['id'] = place_id
            all_locations.append(place)
            place_id += 1
    
    # Save combined JSON to result folder
    json_path = os.path.join(RESULT_DIR, 'places.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({"locations": all_locations}, f, ensure_ascii=False, indent=4)
    
    return all_locations

def save_to_db(locations, db_file='places.db'):
    """Convert locations to DataFrame and save to SQLite database"""
    cleaned_data = []
    
    for location in locations:
        props = location.get('properties', {})
        name = props.get('name')
        lat = props.get('lat')
        lon = props.get('lon')
        
        if name and lat and lon:
            # Convert categories list to JSON string for storage
            categories = props.get('categories', [])
            categories_json = json.dumps(categories) if categories else None
            
            cleaned_data.append({
                'Name': name,
                'Latitude': lat,
                'Longitude': lon,
                'Address': props.get('formatted'),
                'Categories': categories_json,  # Store as JSON string
                'Cuisine': props.get('catering', {}).get('cuisine'),
                'Opening_Hours': props.get('opening_hours'),
                'Distance': props.get('distance')
            })
    
    df = pd.DataFrame(cleaned_data)
    db_path = os.path.join(RESULT_DIR, db_file)
    
    with sqlite3.connect(db_path) as conn:
        df.to_sql('places', conn, if_exists='replace', index=False)
        # Create index on Name column for faster searches
        conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON places(Name)")
        # Add Image_URLs column if it doesn't exist
        try:
            conn.execute("ALTER TABLE places ADD COLUMN Image_URLs TEXT")
        except:
            pass  # Column already exists
        conn.commit()
    
    print(f"✅ Saved {len(df)} places to {db_path}")
    return df

if __name__ == "__main__":
    # Fetch and save places
    locations = fetch_places("HCMUS", radius=5000, limit=10)
    df = save_to_db(locations)
    print(df.head())
