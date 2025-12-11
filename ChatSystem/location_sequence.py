import sqlite3 
import os 
import random
import math

class LocationSequence:
    # Define the path to the database at class level
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    RESULT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'DataCollector', 'result')

    def __init__(self):
        self.sequence = []

    def append(self, position , ID ):
        if position < 0 or position > len(self.sequence):
            raise IndexError("Location out of bounds")
        self.sequence.insert(position, ID)
    
    def pop(self, position):
        self.sequence.pop(position) 
    
    def __str__(self):
        """Return a string representation of the sequence with place names from database"""
        if not self.sequence:
            return "LocationSequence: []"
        
        db_path = os.path.join(self.RESULT_DIR, 'places.db')
        place_names = []
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for place_id in self.sequence:
                cursor.execute("SELECT Title FROM places WHERE rowid = ?", (place_id,))
                result = cursor.fetchone()
                if result:
                    place_names.append(f"{place_id}: {result[0]}")
                else:
                    place_names.append(f"{place_id}: [Not Found]")
        
        return f"LocationSequence: [{', '.join(place_names)}]"
    
    def clear_sequence(self):
        self.sequence = []

    def get_sequence(self):
        return self.sequence

    # --- direct DB helpers (no external import) ---
    def id_to_name(self, place_id):
        """Return the name for a given rowid, or None if not found."""
        db_path = os.path.join(self.RESULT_DIR, 'places.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Title FROM places WHERE rowid = ?", (place_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def search_by_name(self, name, exact=True, limit=10):
        """Return IDs with exact name first (if any), then fuzzy matches to fill up to limit."""
        if not name or not str(name).strip():
            return []

        db_path = os.path.join(self.RESULT_DIR, 'places.db')
        exclude_ids = set(self.sequence)
        results = []
        seen = set()

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            if exact:
                cursor.execute("SELECT rowid FROM places WHERE Title = ?", (name,))
                exact_rows = [row[0] for row in cursor.fetchall()]
                for rid in exact_rows:
                    if rid in exclude_ids or rid in seen:
                        continue
                    seen.add(rid)
                    results.append(rid)
                if len(results) >= limit:
                    return results[:limit]

            # Fuzzy search to fill remaining slots, sorted by similarity (more keyword hits, then shorter name)
            keywords = name.lower().split()
            remaining = max(0, limit - len(results))
            if keywords and remaining > 0:
                like_fragments = ["LOWER(Title) LIKE ?" for _ in keywords]
                score_expr = " + ".join(["(LOWER(Title) LIKE ?)"] * len(keywords))
                where_clause = " OR ".join(like_fragments)
                query = f"""
                    SELECT rowid, ({score_expr}) AS score, LENGTH(Title) AS len
                    FROM places
                    WHERE {where_clause}
                    ORDER BY score DESC, len ASC
                    LIMIT ?
                """
                patterns = [f"%{kw}%" for kw in keywords]
                params = patterns + patterns + [remaining]
                cursor.execute(query, params)
                for row in cursor.fetchall():
                    rid = row[0]
                    if rid in exclude_ids or rid in seen:
                        continue
                    seen.add(rid)
                    results.append(rid)

        return results[:limit]
    def get_suggest_category(self) :
        categories = ['restaurant', 'cafe', 'bar', 'museum', 'park', 'shopping', 'theater', 'gallery']
        return random.choice(categories)
    def suggest_for_position(self, pos, category=None, limit=5):
        """
        Suggest IDs to place at insertion position `pos` (no insertion performed).
        - If sequence empty: return top IDs by category (or any) limited by `limit`.
        - If inserting at begin: nearest to first item.
        - If inserting at end: nearest to last item.
        - If inserting between: minimize distance to both neighbors.
        Always excludes IDs already in the current sequence.
        """

        exclude_ids = set(self.sequence)
        db_path = os.path.join(self.RESULT_DIR, 'places.db')

        def _coords_rating(place_id):
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT location_lat, location_lng, rating FROM places WHERE rowid = ?", (place_id,))
                row = cursor.fetchone()
                return (row[0], row[1], row[2]) if row else None

        def _near(anchor_id):
            coords = _coords_rating(anchor_id)
            if not coords:
                return []
            lat, lon, _ = coords
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                radius_meters = 15000
                query = """
                    SELECT rowid, rating,
                    (6371000 * acos(cos(radians(?)) * cos(radians(location_lat)) * 
                    cos(radians(location_lng) - radians(?)) + 
                    sin(radians(?)) * sin(radians(location_lat)))) AS distance
                    FROM places
                    WHERE rowid != ? {cat_filter}
                    ORDER BY distance
                    LIMIT ?
                """
                cat_clause = ""
                params = [lat, lon, lat, anchor_id]
                if category:
                    cat_clause = "AND Categories LIKE ?"
                    params.append(f"%{category}%")
                params.append(limit + len(exclude_ids))
                cursor.execute(query.format(cat_filter=cat_clause), params)
                scored = []
                for row in cursor.fetchall():
                    rid = row["rowid"]
                    if rid in exclude_ids:
                        continue
                    rating = row["rating"] if row["rating"] not in (None, 0) else 1
                    score = row["distance"] / rating
                    scored.append((score, rid))
                scored.sort(key=lambda x: x[0])
                return [rid for _, rid in scored[:limit]]

        def _between(a_id, b_id):
            a_coords = _coords_rating(a_id)
            b_coords = _coords_rating(b_id)
            if not a_coords or not b_coords:
                return []
            a_lat, a_lon, _ = a_coords
            b_lat, b_lon, _ = b_coords
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Fetch a wider set ordered by distance to prev, then sort in Python by combined cost
                base_limit = (limit + len(exclude_ids)) * 3
                query = """
                    SELECT rowid, rating,
                    (6371000 * acos(cos(radians(?)) * cos(radians(location_lat)) * 
                    cos(radians(location_lng) - radians(?)) + 
                    sin(radians(?)) * sin(radians(location_lat)))) AS dist_prev
                    FROM places
                    WHERE rowid NOT IN (?, ?)
                    {cat_filter}
                    ORDER BY dist_prev
                    LIMIT ?
                """
                cat_clause = ""
                params = [a_lat, a_lon, a_lat, a_id, b_id]
                if category:
                    cat_clause = "AND Categories LIKE ?"
                    params.append(f"%{category}%")
                params.append(base_limit)
                cursor.execute(query.format(cat_filter=cat_clause), params)
                candidates = []
                for row in cursor.fetchall():
                    rid = row["rowid"]
                    if rid in exclude_ids:
                        continue
                    candidates.append(rid)

            # Compute cost = dist(a,p) + dist(p,b)
            scored = []
            for rid in candidates:
                coords = _coords_rating(rid)
                if not coords:
                    continue
                p_lat, p_lon, rating = coords
                rating = rating if rating not in (None, 0) else 1
                def _dist(lat1, lon1, lat2, lon2):
                    return 6371000 * (math.acos(math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                                                math.cos(math.radians(lon2 - lon1)) +
                                                math.sin(math.radians(lat1)) * math.sin(math.radians(lat2))))
                cost = (_dist(a_lat, a_lon, p_lat, p_lon) + _dist(p_lat, p_lon, b_lat, b_lon)) / rating
                scored.append((cost, rid))
            scored.sort(key=lambda x: x[0])
            return [rid for _, rid in scored[:limit]]

        # Case handling
        if not self.sequence:
            # No anchors: fall back to category list or any
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                if category:
                    cursor.execute(
                        "SELECT rowid FROM places WHERE Categories LIKE ? LIMIT ?",
                        (f"%{category}%", limit)
                    )
                else:
                    cursor.execute("SELECT rowid FROM places LIMIT ?", (limit,))
                return [row[0] for row in cursor.fetchall() if row[0] not in exclude_ids][:limit]

        if pos <= 0:
            return _near(self.sequence[0])

        if pos >= len(self.sequence):
            return _near(self.sequence[-1])

        # Between two nodes
        prev_id = self.sequence[pos-1]
        next_id = self.sequence[pos]
        return _between(prev_id, next_id)
    def suggest_around(self, lat, lon, limit=5, category=None):
        if category is None:
            category = random.choice(['restaurant', 'cafe', 'bar', 'museum', 'park'])
        
        # Connect to the database
        db_path = os.path.join(self.RESULT_DIR, 'places.db')
        with sqlite3.connect(db_path) as conn:  
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query to find places within a certain radius (e.g., 5km)
            radius_meters = 15000
            query = """
            SELECT rowid, rating, 
            (6371000 * acos(cos(radians(?)) * cos(radians(location_lat)) * 
            cos(radians(location_lng) - radians(?)) + 
            sin(radians(?)) * sin(radians(location_lat)))) AS distance 
            FROM places 
            WHERE Categories LIKE ? 
            AND (6371000 * acos(cos(radians(?)) * cos(radians(location_lat)) * 
                cos(radians(location_lng) - radians(?)) + 
                sin(radians(?)) * sin(radians(location_lat)))) < ?
            ORDER BY distance 
            LIMIT ?
            """
            cursor.execute(query, (lat, lon, lat, f"%{category}%", lat, lon, lat, radius_meters, limit))
            results = cursor.fetchall()
            scored = []
            for row in results:
                rating = row["rating"] if row["rating"] not in (None, 0) else 1
                score = row["distance"] / rating
                scored.append((score, row["rowid"]))
            scored.sort(key=lambda x: x[0])
            return [rid for _, rid in scored[:limit]]
    # def suggest_itinerary_to_sequence(self, limit=5):
        
        
if __name__ == "__main__": 
    loc_seq = LocationSequence()

    # Test search_by_name
    print("\n=== Testing search_by_name ===")
    ids = loc_seq.search_by_name("Khách sạn Nikko SaiGon", exact=False, limit=10)
    print(f"IDs for 'Khách sạn Nikko SaiGon' (excluding current sequence): {ids}")
    for pid in ids:
        name = loc_seq.id_to_name(pid)
        print(f" - {pid}: {name}")

    # Test suggest_for_position: print id, name, and score (distance/rating)
    print("\n=== Testing suggest_for_position (score = distance/rating) ===")
    db_path = os.path.join(loc_seq.RESULT_DIR, 'places.db')
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rowid FROM places LIMIT 3")
        seed_ids = [row[0] for row in cursor.fetchall()]

    if len(seed_ids) < 2:
        print("Not enough places in DB to run suggest_for_position test.")
    else:
        # Seed the sequence with two anchors
        loc_seq.sequence = [seed_ids[0], seed_ids[1]]
        insert_pos = 1  # between the two anchors
        suggestions = loc_seq.suggest_for_position(pos=insert_pos, limit=5)

        def _coords_rating(pid):
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT location_lat, location_lng, rating FROM places WHERE rowid = ?", (pid,))
                row = c.fetchone()
                return (row[0], row[1], row[2]) if row else None

        def _dist(lat1, lon1, lat2, lon2):
            return 6371000 * (math.acos(math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                                        math.cos(math.radians(lon2 - lon1)) +
                                        math.sin(math.radians(lat1)) * math.sin(math.radians(lat2))))

        prev_id = loc_seq.sequence[insert_pos - 1]
        next_id = loc_seq.sequence[insert_pos]
        prev_coords = _coords_rating(prev_id)
        next_coords = _coords_rating(next_id)

        if not prev_coords or not next_coords:
            print("Could not fetch anchor coordinates; skipping score print.")
        else:
            print(f"Anchors: prev={prev_id}, next={next_id}")
            for rid in suggestions:
                coords = _coords_rating(rid)
                if not coords:
                    continue
                p_lat, p_lon, rating = coords
                rating = rating if rating not in (None, 0) else 1
                score = (_dist(prev_coords[0], prev_coords[1], p_lat, p_lon) +
                         _dist(p_lat, p_lon, next_coords[0], next_coords[1])) / rating
                name = loc_seq.id_to_name(rid)
                print(f" - id={rid}, name={name}, score={score:.2f}")
