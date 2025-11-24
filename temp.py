"""
Extract Info Module
Extracts journey planning information from natural language using Gemini API.
"""

import json
import requests
import math
import random
from datetime import datetime, timedelta

# ============================================================================
# API KEY
# ============================================================================
GEMINI_KEY = 'AIzaSyAuZjU6TJbEsC1ILHAsAGyG7gPFb5XGqCA'
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
            params={'text': location_name , 'apiKey': GEOAPIFY_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('features'):
                coords = data['features'][0].get('geometry', {}).get('coordinates', [])
                if len(coords) >= 2:
                    return {'lat': coords[1], 'lon': coords[0]}
        return None
    except Exception:
        return None

if __name__ == "__main__":
    print(geocode_location("ba na hill"))