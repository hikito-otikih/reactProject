import googlemaps
import os

# 1. Setup Client
API_KEY = '01C314-FDFC9D-66957B'
gmaps = googlemaps.Client(key=API_KEY)

def get_place_image(search_query, save_path="place_image.jpg"):
    try:
        # Step 1: Find the place to get its 'place_id'
        print(f"Searching for: {search_query}...")
        search_result = gmaps.places(query=search_query)
        
        if not search_result['results']:
            print("No results found.")
            return

        place = search_result['results'][0]
        place_id = place['place_id']
        place_name = place['name']
        print(f"Found: {place_name} ({place_id})")

        # Step 2: Get Place Details to find 'photos' metadata
        # We need the 'photo_reference' from the details
        details = gmaps.place(place_id=place_id, fields=['photo'])
        
        if 'photos' not in details['result']:
            print("No photos available for this location.")
            return

        # Get the first photo reference
        photo_ref = details['result']['photos'][0]['photo_reference']
        
        # Step 3: Download the actual image
        # max_width/max_height is required (max 1600)
        print("Downloading image...")
        photo_data = gmaps.places_photo(photo_reference=photo_ref, max_width=1600)

        # Write the raw data to a file
        with open(save_path, 'wb') as f:
            for chunk in photo_data:
                if chunk:
                    f.write(chunk)
        
        print(f"Success! Saved to {save_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example Usage
get_place_image("Eiffel Tower Paris")