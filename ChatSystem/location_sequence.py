import sqlite3 
import os 
import random
import math

class LocationSequence:
    # Define the path to the database at class level
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    RESULT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'DataCollector', 'result')

    def __init__(self):
        self.start_coordinate = [10.7628356, 106.6824824]  # lat , lon  of hcmus by default
        self.sequence = []
    def load_sequence(self, start_coordinate, sequence):
        self.start_coordinate = start_coordinate
        self.sequence = sequence
    def append(self, position , ID ):
        if position < 0 or position > len(self.sequence):
            raise IndexError("Location out of bounds")
        self.sequence.insert(position, ID)

    def pop(self, position):
        self.sequence.pop(position) 

    def input_start_coordinate(self, lat: float, lon: float):
        self.start_coordinate = [lat, lon]
    def get_start_coordinate(self):
        return self.start_coordinate
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
        categories = ['catering', 'commercial', 'service', 'entertainment', 'leisure','tourism','heritage']
        return random.choice(categories)
    def suggest_for_position(self, pos=-1, category=None, limit=5):
        """
        Suggest IDs to place at insertion position `pos` (no insertion performed).
        - Virtual start location lives at index 0 using `start_coordinate` (not in DB).
        - If sequence empty: nearest to start.
        - If inserting at begin: minimize start → candidate → first item.
        - If inserting at end: nearest to last item.
        - If inserting between: minimize distance between neighbors.
        Always excludes IDs already in the current sequence.
        """

        if limit <= 0:
            return []

        if pos == -1:
            pos = len(self.sequence) - 1

        exclude_ids = set(self.sequence)
        db_path = os.path.join(self.RESULT_DIR, 'places.db')

        def _dist(lat1, lon1, lat2, lon2):
            return 6371000 * (math.acos(math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                                        math.cos(math.radians(lon2 - lon1)) +
                                        math.sin(math.radians(lat1)) * math.sin(math.radians(lat2))))

        def _coords_rating(place_id):
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT location_lat, location_lng, rating FROM places WHERE rowid = ?", (place_id,))
                row = cursor.fetchone()
                return (row[0], row[1], row[2]) if row else None

        def _fetch_candidates(anchor_lat, anchor_lon, base_limit):
            exclude_clause = "1=1"
            params = [anchor_lat, anchor_lon, anchor_lat]
            if exclude_ids:
                placeholders = ",".join(["?"] * len(exclude_ids))
                exclude_clause = f"rowid NOT IN ({placeholders})"
                params.extend(list(exclude_ids))
            cat_clause = ""
            if category:
                cat_clause = "AND Categories LIKE ?"
                params.append(f"%{category}%")
            params.append(base_limit)

            query = f"""
                SELECT rowid, rating,
                (6371000 * acos(cos(radians(?)) * cos(radians(location_lat)) *
                cos(radians(location_lng) - radians(?)) +
                sin(radians(?)) * sin(radians(location_lat)))) AS dist_prev
                FROM places
                WHERE {exclude_clause}
                {cat_clause}
                ORDER BY dist_prev
                LIMIT ?
            """
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()

        def _near_coords(anchor_lat, anchor_lon):
            rows = _fetch_candidates(anchor_lat, anchor_lon, limit + len(exclude_ids))
            scored = []
            for row in rows:
                rid = row["rowid"]
                if rid in exclude_ids:
                    continue
                rating = row["rating"] if row["rating"] not in (None, 0) else 1
                score = row["dist_prev"] / rating
                scored.append((score, rid))
            scored.sort(key=lambda x: x[0])
            return [rid for _, rid in scored[:limit]]

        def _between_coords(a_lat, a_lon, b_lat, b_lon):
            rows = _fetch_candidates(a_lat, a_lon, (limit + len(exclude_ids)) * 3)
            scored = []
            for row in rows:
                rid = row["rowid"]
                if rid in exclude_ids:
                    continue
                coords = _coords_rating(rid)
                if not coords:
                    continue
                p_lat, p_lon, rating = coords
                rating = rating if rating not in (None, 0) else 1
                cost = (_dist(a_lat, a_lon, p_lat, p_lon) + _dist(p_lat, p_lon, b_lat, b_lon)) / rating
                scored.append((cost, rid))
            scored.sort(key=lambda x: x[0])
            return [rid for _, rid in scored[:limit]]

        # Case handling with virtual start
        if not self.sequence:
            s_lat, s_lon = self.start_coordinate
            return _near_coords(s_lat, s_lon)

        if pos <= 0:
            first_coords = _coords_rating(self.sequence[0])
            if not first_coords:
                return []
            s_lat, s_lon = self.start_coordinate
            f_lat, f_lon, _ = first_coords
            return _between_coords(s_lat, s_lon, f_lat, f_lon)

        if pos >= len(self.sequence):
            last_coords = _coords_rating(self.sequence[-1])
            if not last_coords:
                return []
            l_lat, l_lon, _ = last_coords
            return _near_coords(l_lat, l_lon)

        prev_coords = _coords_rating(self.sequence[pos - 1])
        next_coords = _coords_rating(self.sequence[pos])
        if not prev_coords or not next_coords:
            return []
        a_lat, a_lon, _ = prev_coords
        b_lat, b_lon, _ = next_coords
        return _between_coords(a_lat, a_lon, b_lat, b_lon)
    def suggest_around(self, lat, lon, limit=5, category=None):
        if category is None:
            category = random.choice(['catering', 'commercial', 'service', 'entertainment', 'leisure','tourism','heritage'])
        
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
    def suggest_itinerary_to_sequence(self, limit=5):
        """
        Recommend up to `limit` new place IDs to append at the end of the trip.
        - Uses the last ID in the current sequence as the anchor if present; otherwise cold-start by rating.
        - Scoring = distance / rating (rating floored to 1; assumes rating up to 5).
        - Category filtering expects the `Categories` column to store bracketed, comma-separated values like
          "[catering,commercial,service]". We parse and match on lowercase tokens.
        """

        if limit <= 0:
            return []

        db_path = os.path.join(self.RESULT_DIR, 'places.db')
        exclude_ids = set(self.sequence)

        def _parse_categories(cat_str):
            if not cat_str:
                return []
            s = str(cat_str).strip()
            if s.startswith('[') and s.endswith(']'):
                s = s[1:-1]
            return [token.strip().lower() for token in s.split(',') if token.strip()]

        def _dist(lat1, lon1, lat2, lon2):
            return 6371000 * (math.acos(math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                                        math.cos(math.radians(lon2 - lon1)) +
                                        math.sin(math.radians(lat1)) * math.sin(math.radians(lat2))))

        anchor_id = self.sequence[-1] if self.sequence else None
        candidates = []
        pool = max(limit * 5, limit + 5)

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            anchor_coords = None
            if anchor_id:
                cur.execute("SELECT location_lat, location_lng FROM places WHERE rowid = ?", (anchor_id,))
                anchor_row = cur.fetchone()
                if not anchor_row:
                    return []
                anchor_coords = (anchor_row["location_lat"], anchor_row["location_lng"])
            else:
                anchor_coords = tuple(self.start_coordinate) if self.start_coordinate else None

            if anchor_coords:
                a_lat, a_lon = anchor_coords
                cur.execute(
                    """
                    SELECT rowid, rating, Categories, location_lat, location_lng,
                    (6371000 * acos(cos(radians(?)) * cos(radians(location_lat)) *
                    cos(radians(location_lng) - radians(?)) +
                    sin(radians(?)) * sin(radians(location_lat)))) AS distance
                    FROM places
                    ORDER BY distance
                    LIMIT ?
                    """,
                    (a_lat, a_lon, a_lat, pool)
                )
                for row in cur.fetchall():
                    rid = row["rowid"]
                    if rid in exclude_ids or (anchor_id and rid == anchor_id):
                        continue
                    cats = _parse_categories(row["Categories"])
                    rating = row["rating"] if row["rating"] not in (None, 0) else 1
                    score = row["distance"] / rating
                    candidates.append((score, rid, cats))
            else:
                cur.execute(
                    "SELECT rowid, rating, Categories, location_lat, location_lng FROM places ORDER BY rating DESC LIMIT ?",
                    (pool,)
                )
                for row in cur.fetchall():
                    rid = row["rowid"]
                    if rid in exclude_ids:
                        continue
                    cats = _parse_categories(row["Categories"])
                    rating = row["rating"] if row["rating"] not in (None, 0) else 1
                    score = 1 / rating
                    candidates.append((score, rid, cats))

        # If a category filter string is desired, enforce it here on parsed cats
        # (user can modify signature to pass category; keeping simple for now).

        candidates.sort(key=lambda x: x[0])
        return [rid for _, rid, _ in candidates[:limit]]


        
if __name__ == "__main__": 
    def run_tests():
        print("\n=== LocationSequence smoke tests ===")
        loc_seq = LocationSequence()
        db_path = os.path.join(loc_seq.RESULT_DIR, 'places.db')
        if not os.path.exists(db_path):
            print("No places.db found; skipping DB-dependent tests.")
            return

        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT rowid FROM places LIMIT 5")
            seed_ids = [row[0] for row in cur.fetchall()]

        def show(msg):
            print(f"- {msg}")

        # append / pop / clear / get_sequence
        loc_seq.append(0, 9999)
        show(f"append -> {loc_seq.get_sequence()}")
        loc_seq.pop(0)
        show(f"pop -> {loc_seq.get_sequence()}")
        loc_seq.clear_sequence()
        show(f"clear -> {loc_seq.get_sequence()}")

        # input_start_coordinate
        # loc_seq.input_start_coordinate(11.0, 107.0)
        show(f"start_coordinate -> {loc_seq.start_coordinate}")

        # id_to_name and search_by_name
        if seed_ids:
            name = loc_seq.id_to_name(seed_ids[0])
            show(f"id_to_name({seed_ids[0]}) -> {name}")
        ids = loc_seq.search_by_name("Quán ăn", exact=False, limit=5)
        show(f"search_by_name('Quán ăn') -> {ids}")

        # suggest_for_position: empty sequence uses start_coordinate
        loc_seq.clear_sequence()
        s_empty = loc_seq.suggest_for_position(limit=3)
        show(f"suggest_for_position (empty, start anchor) -> {s_empty}")

        # suggest_for_position: between two anchors if we have at least 2 seeds
        if len(seed_ids) >= 2:
            loc_seq.sequence = [seed_ids[0], seed_ids[1]]
            s_between = loc_seq.suggest_for_position(pos=1, limit=3)
            show(f"suggest_for_position (between) -> {s_between}")

        # suggest_around
        s_around = loc_seq.suggest_around(lat=loc_seq.start_coordinate[0], lon=loc_seq.start_coordinate[1], limit=3)
        show(f"suggest_around -> {s_around}")

        # suggest_itinerary_to_sequence: empty uses start_coordinate, then with anchor
        loc_seq.clear_sequence()
        itin_cold = loc_seq.suggest_itinerary_to_sequence(limit=3)
        show(f"suggest_itinerary_to_sequence (cold start) -> {itin_cold}")
        if seed_ids:
            loc_seq.sequence = [seed_ids[0]]
            itin_anchor = loc_seq.suggest_itinerary_to_sequence(limit=3)
            show(f"suggest_itinerary_to_sequence (with anchor) -> {itin_anchor}")

        print("=== Tests finished ===\n")

    run_tests()
