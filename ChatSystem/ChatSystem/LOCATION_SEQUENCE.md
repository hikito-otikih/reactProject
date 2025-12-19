# LocationSequence: Quick Guide

This class manages an ordered itinerary of place IDs backed by `DataCollector/result/places.db`.

## Database expectations
- SQLite DB at `DataCollector/result/places.db`
- Required columns: `rowid`, `Title`, `location_lat`, `location_lng`, `rating`, `Categories`
- `Categories` is a text field storing bracketed, comma-separated values, e.g. `[catering,commercial,service]`.
- `rating` is treated as up to 5; if 0/NULL it is floored to 1 for scoring.

## Core methods
- `append(position, ID)`: Insert an ID at a position (IndexError if out of bounds).
- `pop(position)`: Remove ID at position.
- `clear_sequence()`: Empty the sequence.
- `get_sequence()`: Return the list of IDs.
- `__str__()`: Pretty-print IDs with names looked up from the DB.

## Lookup helpers
- `id_to_name(place_id)`: Return the `Title` for a `rowid`, or `None` if missing.
- `search_by_name(name, exact=True, limit=10)`: Exact title match first; then fuzzy keyword LIKEs to fill remaining slots; always excludes IDs already in the sequence.

[id0,....,id1,...,id2]

[start,...]

## Suggestion methods

[id1,id2,id3] 

- `suggest_for_position(pos=, category=None, limit=5)`
  - Empty sequence: returns first `limit` matches (category-filtered if provided).
  - `pos <= 0`: nearest to the first item.
  - `pos >= len(sequence)`: nearest to the last item.
  - Between two items: minimizes distance to both neighbors.
  - Scoring: `distance / rating` (rating floored to 1); excludes IDs already in the sequence.
  - Category filtering uses `Categories LIKE '%<category>%'`.
- `suggest_around(lat, lon, limit=5, category=None)`
  - Finds nearby places around a coordinate; scoring is `distance / rating`; category via `Categories LIKE`.
  - 
- `suggest_itinerary_to_sequence(limit=5)`
  - Append-style recommendations: uses the last stop as anchor (if any), otherwise cold-starts by rating.
  - Scoring: `distance / rating` (rating floored to 1; assumes rating up to 5).
  - Parses `Categories` as bracketed list strings (e.g., `[catering,commercial,service]`).
  - Returns up to `limit` new IDs; does not mutate the sequence itself.
- `get_suggest_category()`
  - Returns a random category from a preset list.

## Quick smoke test
Run directly:
```
python ChatSystem/location_sequence.py
```
This executes sample runs for `search_by_name`, `suggest_for_position`, and `suggest_itinerary_to_sequence`, printing IDs, names, and scores.

## Notes and caveats
- Missing/invalid coordinates skip a candidate silently.
- Category filtering uses the `Categories` text field; ensure your stored categories follow the bracketed, comma-separated format.
- Suggestion methods return IDs; the caller is responsible for appending them to the sequence.
