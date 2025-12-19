import sqlite3 
import os 
import random
import math
import re

try:
    from rapidfuzz import fuzz
except Exception:
    fuzz = None

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
                cursor.execute("SELECT title FROM places WHERE rowid = ?", (place_id,))
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
            cursor.execute("SELECT title FROM places WHERE rowid = ?", (place_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def search_by_name(self, name, exact=True, limit=10):
        """Return IDs matching a place title.

        Behavior:
        - If `exact=True`, return exact-title hits first.
        - Fill remaining slots with best fuzzy matches using RapidFuzz (if available).
        - Always excludes IDs already present in the current sequence.
        """

        if limit <= 0:
            return []
        if not name or not str(name).strip():
            return []

        query_text = str(name).strip()
        db_path = os.path.join(self.RESULT_DIR, 'places.db')
        exclude_ids = set(self.sequence)
        results = []
        seen = set()

        def _normalize_text(s: str) -> str:
            if s is None:
                return ""
            s = str(s).lower()
            s = re.sub(r"[^0-9a-z]+", " ", s)
            parts = [p for p in s.split() if p and not p.isdigit()]
            return " ".join(parts)

        def _title_similarity(q: str, t: str) -> float:
            qn = _normalize_text(q)
            tn = _normalize_text(t)
            if not qn or not tn:
                return 0.0
            if fuzz is None:
                import difflib
                return difflib.SequenceMatcher(None, qn, tn).ratio()
            # token_set_ratio works well for partial/extra tokens
            return fuzz.token_set_ratio(qn, tn) / 100.0

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if exact:
                cursor.execute("SELECT rowid FROM places WHERE title = ?", (query_text,))
                for row in cursor.fetchall():
                    rid = row[0]
                    if rid in exclude_ids or rid in seen:
                        continue
                    seen.add(rid)
                    results.append(rid)
                if len(results) >= limit:
                    return results[:limit]

            remaining = max(0, limit - len(results))
            if remaining <= 0:
                return results[:limit]

            # DB is small in this project, so scoring all titles is safe and gives best matches.
            cursor.execute("SELECT rowid, title FROM places")
            scored = []
            for row in cursor.fetchall():
                rid = row["rowid"]
                if rid in exclude_ids or rid in seen:
                    continue
                title = row["title"]
                sim = _title_similarity(query_text, title)
                scored.append((sim, len(title) if title else 10**9, rid))

            # Highest similarity first; tie-break by shorter title.
            scored.sort(key=lambda x: (-x[0], x[1], x[2]))
            for sim, _, rid in scored:
                if len(results) >= limit:
                    break
                # Optional guard: if query is very specific, you can raise this threshold.
                # For now we accept any similarity and just return the best-ranked.
                results.append(rid)
                seen.add(rid)

        return results[:limit]
    def get_suggest_category(self) :
        categories = [
                    "accessories", "accommodation", "activity", "agency", "alcohol", "alteration",
                    "amusement", "antique", "apartment", "art", "asian", "attraction",
                    "bakery", "bank", "bar", "barbecue", "barber", "bean",
                    "bistro", "bookstore", "breakfast", "brunch", "buddhist", "buffet",
                    "builder", "cafe", "cake", "car", "care", "caterer",
                    "catering", "catholic", "center", "chicken", "chinese", "church",
                    "clinic", "clothing", "cocktail", "coffee", "commercial", "company",
                    "complex", "consultant", "convenience", "corporate", "cosmetics", "country",
                    "court", "cream", "curry", "deck", "department", "dessert",
                    "drink", "electronics", "entertainment", "equipment", "estate", "european",
                    "fabrication", "facial", "family", "fashion", "fast", "food",
                    "gallery", "german", "gift", "gourmet", "grill", "grocery",
                    "gym", "halal", "hawker", "health", "heritage", "historical",
                    "history", "home", "hospitality", "hot", "ice", "improvement",
                    "indian", "industrial", "information", "institution", "italian", "izakaya",
                    "japanese", "kitchen", "korean", "landmark", "laundromat", "laundry",
                    "leisure", "local", "log", "lounge", "machine", "mall",
                    "manufacturer", "manufacturing", "media", "memorial", "mobile", "modern",
                    "monopoly", "mung", "museum", "natural", "noodle", "observation",
                    "office", "operator", "organizer", "outdoor", "packaging", "paint",
                    "pancake", "park", "patisserie", "pharmaceutical", "pho", "pickleball",
                    "pizza", "plastic", "porridge", "pot", "products", "protestant",
                    "pub", "real", "religion", "religious", "rental", "restaurant",
                    "retail", "rice", "sandwich", "sauna", "school", "scooter",
                    "seafood", "service", "services", "shared", "shop", "shopping",
                    "showroom", "skin", "spa", "sports", "stall", "store",
                    "supermarket", "supplier", "sushi", "sweets", "taco", "takeout",
                    "temple", "tiffin", "tour", "tourism", "tourist", "toy",
                    "trade", "travel", "udon", "vegan", "vegetarian", "vietnamese",
                    "war", "western", "wine", "womens", "yakiniku", "yakitori", "zoo"
                    ]
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

        def _normalize_text(s: str) -> str:
            if s is None:
                return ""
            s = str(s).lower()
            # Replace non-alphanumerics with space
            s = re.sub(r"[^0-9a-z]+", " ", s)
            parts = [p for p in s.split() if p and not p.isdigit()]
            return " ".join(parts)

        def _title_similarity(query: str, title: str) -> float:
            """Return similarity in [0, 1]. Uses RapidFuzz when available."""
            q = _normalize_text(query)
            t = _normalize_text(title)
            if not q or not t:
                return 0.0
            if fuzz is None:
                # Safe fallback (lower quality) if rapidfuzz isn't available
                import difflib
                return difflib.SequenceMatcher(None, q, t).ratio()
            return fuzz.token_set_ratio(q, t) / 100.0

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

        def _fetch_candidates(anchor_lat, anchor_lon, base_limit, filter_mode=None):
            exclude_clause = "1=1"
            params = [anchor_lat, anchor_lon, anchor_lat]
            if exclude_ids:
                placeholders = ",".join(["?"] * len(exclude_ids))
                exclude_clause = f"rowid NOT IN ({placeholders})"
                params.extend(list(exclude_ids))
            filter_clause = ""
            if category and filter_mode == "category":
                filter_clause = "AND categories LIKE ?"
                params.append(f"%{category}%")
            elif category and filter_mode == "title":
                # Title fuzzy search is handled in Python using similarity scoring.
                filter_clause = ""
            params.append(base_limit)

            query = f"""
                SELECT rowid, rating, title,
                (6371000 * acos(cos(radians(?)) * cos(radians(location_lat)) *
                cos(radians(location_lng) - radians(?)) +
                sin(radians(?)) * sin(radians(location_lat)))) AS dist_prev
                FROM places
                WHERE {exclude_clause}
                {filter_clause}
                ORDER BY dist_prev
                LIMIT ?
            """
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()

        def _near_coords(anchor_lat, anchor_lon):
            results = []
            seen = set(exclude_ids)

            def _score_rows(rows):
                scored = []
                for row in rows:
                    rid = row["rowid"]
                    if rid in seen:
                        continue
                    rating = row["rating"] if row["rating"] not in (None, 0) else 1
                    score = row["dist_prev"] / rating
                    scored.append((score, rid))
                scored.sort(key=lambda x: x[0])
                return scored

            def _score_rows_title_fuzzy(rows, sim_threshold=0.45, sim_lambda_m=2000.0):
                """Rank by (distance/rating + penalty based on (1-similarity))."""
                scored = []
                for row in rows:
                    rid = row["rowid"]
                    if rid in seen:
                        continue
                    sim = _title_similarity(category, row["title"])
                    if sim < sim_threshold:
                        continue
                    rating = row["rating"] if row["rating"] not in (None, 0) else 1
                    base_cost = row["dist_prev"] / rating
                    cost = base_cost + sim_lambda_m * (1.0 - sim)
                    scored.append((cost, rid))
                scored.sort(key=lambda x: x[0])
                return scored

            # 1) Try category match first (if provided)
            if category:
                rows = _fetch_candidates(anchor_lat, anchor_lon, limit + len(exclude_ids), filter_mode="category")
                for _, rid in _score_rows(rows):
                    results.append(rid)
                    seen.add(rid)
                    if len(results) >= limit:
                        return results[:limit]

                # 2) Fallback: match by Title if not enough
                remaining = max(0, limit - len(results))
                if remaining > 0:
                    # Pull a nearby pool, then filter+rank by fuzzy title similarity
                    pool = max(200, remaining * 20, remaining + len(exclude_ids))
                    rows2 = _fetch_candidates(anchor_lat, anchor_lon, pool, filter_mode="title")
                    for _, rid in _score_rows_title_fuzzy(rows2):
                        results.append(rid)
                        seen.add(rid)
                        if len(results) >= limit:
                            return results[:limit]

                # If a query was provided, do NOT backfill with unrelated rows.
                return results[:limit]

            # No category provided: original behavior
            rows = _fetch_candidates(anchor_lat, anchor_lon, limit + len(exclude_ids), filter_mode=None)
            for _, rid in _score_rows(rows):
                results.append(rid)
                if len(results) >= limit:
                    break
            return results[:limit]

        def _between_coords(a_lat, a_lon, b_lat, b_lon):
            results = []
            seen = set(exclude_ids)

            def _score_rows(rows):
                scored = []
                for row in rows:
                    rid = row["rowid"]
                    if rid in seen:
                        continue
                    coords = _coords_rating(rid)
                    if not coords:
                        continue
                    p_lat, p_lon, rating = coords
                    rating = rating if rating not in (None, 0) else 1
                    cost = (_dist(a_lat, a_lon, p_lat, p_lon) + _dist(p_lat, p_lon, b_lat, b_lon)) / rating
                    scored.append((cost, rid))
                scored.sort(key=lambda x: x[0])
                return scored

            def _score_rows_title_fuzzy(rows, sim_threshold=0.45, sim_lambda_m=2000.0):
                scored = []
                for row in rows:
                    rid = row["rowid"]
                    if rid in seen:
                        continue
                    sim = _title_similarity(category, row["title"])
                    if sim < sim_threshold:
                        continue
                    coords = _coords_rating(rid)
                    if not coords:
                        continue
                    p_lat, p_lon, rating = coords
                    rating = rating if rating not in (None, 0) else 1
                    base_cost = (_dist(a_lat, a_lon, p_lat, p_lon) + _dist(p_lat, p_lon, b_lat, b_lon)) / rating
                    cost = base_cost + sim_lambda_m * (1.0 - sim)
                    scored.append((cost, rid))
                scored.sort(key=lambda x: x[0])
                return scored

            base = (limit + len(exclude_ids)) * 3

            # 1) Try category match first (if provided)
            if category:
                rows = _fetch_candidates(a_lat, a_lon, base, filter_mode="category")
                for _, rid in _score_rows(rows):
                    results.append(rid)
                    seen.add(rid)
                    if len(results) >= limit:
                        return results[:limit]

                # 2) Fallback: match by Title if not enough
                remaining = max(0, limit - len(results))
                if remaining > 0:
                    pool = max(300, base, remaining * 30, remaining + len(exclude_ids))
                    rows2 = _fetch_candidates(a_lat, a_lon, pool, filter_mode="title")
                    for _, rid in _score_rows_title_fuzzy(rows2):
                        results.append(rid)
                        seen.add(rid)
                        if len(results) >= limit:
                            return results[:limit]

                # If a query was provided, do NOT backfill with unrelated rows.
                return results[:limit]

            # No category provided: original behavior
            rows = _fetch_candidates(a_lat, a_lon, base, filter_mode=None)
            for _, rid in _score_rows(rows):
                results.append(rid)
                if len(results) >= limit:
                    break
            return results[:limit]

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
            WHERE categories LIKE ? 
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
        Recommend a sequence of `limit` new place IDs to append at the end of the trip,
        forming a continuous journey (A -> B -> C...) using Directional/Momentum scoring.
        """
        if limit <= 0:
            return []

        db_path = os.path.join(self.RESULT_DIR, 'places.db')
        visited_ids = set(self.sequence)
        journey = []

        def _get_coords_db(cursor, pid):
            cursor.execute("SELECT location_lat, location_lng FROM places WHERE rowid = ?", (pid,))
            row = cursor.fetchone()
            return (row["location_lat"], row["location_lng"]) if row else None

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # --- INITIALIZATION ---
            current_coords = None
            prev_coords = None

            if self.sequence:
                # Current is the last item
                current_coords = _get_coords_db(cur, self.sequence[-1])
                
                if len(self.sequence) >= 2:
                    # Momentum from second-to-last -> last
                    prev_coords = _get_coords_db(cur, self.sequence[-2])
                else:
                    # Momentum from start -> last
                    prev_coords = tuple(self.start_coordinate)
            else:
                # Starting fresh from start_coordinate
                current_coords = tuple(self.start_coordinate)
                prev_coords = None # No direction yet

            # --- GENERATION LOOP ---
            for _ in range(limit):
                if not current_coords:
                    break
                
                c_lat, c_lon = current_coords
                
                # 1. Build Exclusion Clause
                if visited_ids:
                    placeholders = ",".join(["?"] * len(visited_ids))
                    where_clause = f"rowid NOT IN ({placeholders})"
                    params = [c_lat, c_lon, c_lat] + list(visited_ids)
                else:
                    where_clause = "1=1"
                    params = [c_lat, c_lon, c_lat]

                # 2. Fetch Candidates (Top 30 nearest)
                query = f"""
                    SELECT rowid, rating, location_lat, location_lng,
                    (6371000 * acos(cos(radians(?)) * cos(radians(location_lat)) *
                    cos(radians(location_lng) - radians(?)) +
                    sin(radians(?)) * sin(radians(location_lat)))) AS distance
                    FROM places
                    WHERE {where_clause}
                    ORDER BY distance ASC
                    LIMIT 30
                """
                
                cur.execute(query, params)
                candidates = cur.fetchall()
                
                best_step = None
                min_cost = float('inf')
                
                # Pre-calculate previous vector if it exists
                vec_prev = None
                if prev_coords:
                    p_lat, p_lon = prev_coords
                    # Vector: (dLat, dLon)
                    vec_prev = (c_lat - p_lat, c_lon - p_lon)
                    # Normalize
                    mag = math.sqrt(vec_prev[0]**2 + vec_prev[1]**2)
                    if mag > 0:
                        vec_prev = (vec_prev[0]/mag, vec_prev[1]/mag)
                    else:
                        vec_prev = None

                for row in candidates:
                    # --- SCORING FORMULA ---
                    # Cost = Distance * RatingPenalty * DirectionPenalty
                    
                    dist = row["distance"]
                    rating = row["rating"] if row["rating"] not in (None, 0) else 1
                    
                    # A. Rating Penalty (Higher rating = lower cost)
                    # 5 stars -> x1, 1 star -> x5
                    rating_penalty = max(1, 6 - rating)
                    
                    # B. Direction Penalty
                    dir_penalty = 1.0
                    if vec_prev:
                        n_lat, n_lon = row["location_lat"], row["location_lng"]
                        vec_next = (n_lat - c_lat, n_lon - c_lon)
                        mag_next = math.sqrt(vec_next[0]**2 + vec_next[1]**2)
                        
                        if mag_next > 0:
                            vec_next = (vec_next[0]/mag_next, vec_next[1]/mag_next)
                            # Dot product for cos(theta)
                            cos_theta = vec_prev[0]*vec_next[0] + vec_prev[1]*vec_next[1]
                            # Clamp for safety
                            cos_theta = max(-1.0, min(1.0, cos_theta))
                            
                            # Penalty: 0 deg -> 1.0, 90 deg -> 2.0, 180 deg -> 3.0
                            dir_penalty = 1.0 + (1.0 - cos_theta)

                    cost = dist * rating_penalty * dir_penalty
                    
                    if cost < min_cost:
                        min_cost = cost
                        best_step = row
                
                if best_step:
                    rid = best_step["rowid"]
                    journey.append(rid)
                    visited_ids.add(rid) # Prevent overlap
                    
                    # Update state for next iteration
                    prev_coords = current_coords
                    current_coords = (best_step["location_lat"], best_step["location_lng"])
                else:
                    break
                    
        return journey


        
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
        ids = loc_seq.search_by_name("123123Vincom 123123123Plaza", exact=False, limit=5)
        show(f"search_by_name('123123Vincom 123123123Plaza') -> {ids}")
        for x in ids : 
            n = loc_seq.id_to_name(x)
            show(f"  id_to_name({x}) -> {n}")
        # suggest_for_position: empty sequence uses start_coordinate
        loc_seq.clear_sequence()
        s_empty = loc_seq.suggest_for_position(limit=3)
        show(f"suggest_for_position (empty, start anchor) -> {s_empty}")

        # suggest_for_position: between two anchors if we have at least 2 seeds
        if len(seed_ids) >= 2:
            loc_seq.sequence = [seed_ids[0], seed_ids[1]]
            s_between = loc_seq.suggest_for_position(category = '100 Vincom' , pos=1, limit=100)
            show(f"suggest_for_position (between) -> {s_between}")
            for x in s_between :
                n = loc_seq.id_to_name(x)
                show(f"  id_to_name({x}) -> {n}")

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
