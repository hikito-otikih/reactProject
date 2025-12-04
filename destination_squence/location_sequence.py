import sqlite3 
import os 
import random

# Define the path to the database
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'DataCollector', 'result')

class LocationSequence:
    sequence = [] 
    def append(ID,position) : 
        if position < 0 or position > len(LocationSequence.sequence):
            raise IndexError("Location out of bounds")
        LocationSequence.sequence.insert(position, ID)
    
    def remove(position) :
        LocationSequence.sequence.pop(position) 
    
    def __str__(self):
        """Return a string representation of the sequence with place names from database"""
        if not LocationSequence.sequence:
            return "LocationSequence: []"
        
        db_path = os.path.join(RESULT_DIR, 'places.db')
        place_names = []
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for place_id in LocationSequence.sequence:
                cursor.execute("SELECT Name FROM places WHERE rowid = ?", (place_id,))
                result = cursor.fetchone()
                if result:
                    place_names.append(f"{place_id}: {result[0]}")
                else:
                    place_names.append(f"{place_id}: [Not Found]")
        
        return f"LocationSequence: [{', '.join(place_names)}]"
    
    def clear():
        LocationSequence.sequence = []
    def get_sequence() :
        return LocationSequence.sequence
    def suggest_around(lat, lon, limit=5, category=None):
        if category is None:
            category = random.choice(['restaurant', 'cafe', 'bar', 'museum', 'park'])
        
        # Connect to the database
        db_path = os.path.join(RESULT_DIR, 'places.db')
        with sqlite3.connect(db_path) as conn:  
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query to find places within a certain radius (e.g., 5km)
            radius_meters = 15000
            query = """
            SELECT rowid, *, 
            (6371000 * acos(cos(radians(?)) * cos(radians(Latitude)) * 
            cos(radians(Longitude) - radians(?)) + 
            sin(radians(?)) * sin(radians(Latitude)))) AS distance 
            FROM places 
            WHERE Categories LIKE ? 
            AND (6371000 * acos(cos(radians(?)) * cos(radians(Latitude)) * 
                 cos(radians(Longitude) - radians(?)) + 
                 sin(radians(?)) * sin(radians(Latitude)))) < ?
            ORDER BY distance 
            LIMIT ?
            """
            cursor.execute(query, (lat, lon, lat, f"%{category}%", lat, lon, lat, radius_meters, limit))
            results = cursor.fetchall()
            return results

    def suggest_after(pos, limit=5, category=None):
        """Suggest places to visit after the location at given position in sequence
        
        Args:
            pos: Position in the current sequence
            limit: Maximum number of suggestions (default: 5)
            category: Category to filter by (optional)
        
        Returns:
            List of nearby places sorted by distance
        """
        if pos < 0 or pos >= len(LocationSequence.sequence):
            raise IndexError("Position out of bounds")
        
        current_id = LocationSequence.sequence[pos]
        
        # Connect to the database
        db_path = os.path.join(RESULT_DIR, 'places.db')
        with sqlite3.connect(db_path) as conn:  
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get current place's coordinates using rowid
            cursor.execute("SELECT Latitude, Longitude FROM places WHERE rowid = ?", (current_id,))
            current_place = cursor.fetchone()
            if not current_place:
                return []
            
            lat, lon = current_place['Latitude'], current_place['Longitude']
            
            # Build the query based on whether category is specified
            radius_meters = 10000
            if category:
                query = """
                SELECT rowid, *, 
                (6371000 * acos(cos(radians(?)) * cos(radians(Latitude)) * 
                cos(radians(Longitude) - radians(?)) + 
                sin(radians(?)) * sin(radians(Latitude)))) AS distance 
                FROM places 
                WHERE rowid != ? 
                AND Categories LIKE ?
                AND (6371000 * acos(cos(radians(?)) * cos(radians(Latitude)) * 
                     cos(radians(Longitude) - radians(?)) + 
                     sin(radians(?)) * sin(radians(Latitude)))) < ?
                ORDER BY distance 
                LIMIT ?
                """
                cursor.execute(query, (lat, lon, lat, current_id, f"%{category}%", lat, lon, lat, radius_meters, limit))
            else:
                query = """
                SELECT rowid, *, 
                (6371000 * acos(cos(radians(?)) * cos(radians(Latitude)) * 
                cos(radians(Longitude) - radians(?)) + 
                sin(radians(?)) * sin(radians(Latitude)))) AS distance 
                FROM places 
                WHERE rowid != ? 
                AND (6371000 * acos(cos(radians(?)) * cos(radians(Latitude)) * 
                     cos(radians(Longitude) - radians(?)) + 
                     sin(radians(?)) * sin(radians(Latitude)))) < ?
                ORDER BY distance 
                LIMIT ?
                """
                cursor.execute(query, (lat, lon, lat, current_id, lat, lon, lat, radius_meters, limit))
            
            results = cursor.fetchall()
            return results

if __name__ == "__main__": 
    # Example usage
    LocationSequence.append(1,0)
    LocationSequence.append(2,1)
    LocationSequence.append(3,2)
    print("Current Sequence:", LocationSequence.get_sequence())
    
    LocationSequence.remove(1)
    print("After Removal:", LocationSequence.get_sequence())
    
    # Test suggest_around
    print("\n=== Testing suggest_around ===")
    suggestions = LocationSequence.suggest_around(10.762622, 106.660172, limit=5)
    print(f"Suggestions around (10.762622, 106.660172):")
    for place in suggestions:
        print(f" - ID: {place['rowid']} | {place['Name']} at ({place['Latitude']}, {place['Longitude']})")
    
    # Test suggest_after
    print("\n=== Testing suggest_after ===")
    if LocationSequence.get_sequence():
        after_suggestions = LocationSequence.suggest_after(0, limit=5)
        print(f"Suggestions after position 0 (ID={LocationSequence.get_sequence()[0]}):")
        for place in after_suggestions:
            print(f" - ID: {place['rowid']} | {place['Name']} at ({place['Latitude']}, {place['Longitude']})")
    
    print(LocationSequence())  