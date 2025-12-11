# LocationSequence Usage Guide

This class manages an ordered list of place IDs backed by `DataCollector/result/places.db`.

## Database expectations
- SQLite DB at `DataCollector/result/places.db`
- Required columns: `rowid`, `Title`, `location_lat`, `location_lng`, `rating`, `Categories`
- `rating` is treated as up to 5; if 0/NULL it is floored to 1 for scoring.
- Category filters in the current code use `Categories LIKE '%<category>%'` (no `cat_*` flag support yet).

## Core methods
- `append(position, ID)`: Insert an ID at a position (IndexError if out of bounds).
- `pop(position)`: Remove ID at position.
- `clear_sequence()`: Empty the sequence.
- `get_sequence()`: Return the list of IDs.
- `__str__()`: Pretty-print IDs with names looked up from the DB.

## Lookup helpers
- `id_to_name(place_id)`: Return the `Title` for a `rowid`, or `None` if missing.
- `search_by_name(name, exact=True, limit=10)`: Exact title match first; then fuzzy keyword LIKEs to fill remaining slots; always excludes IDs already in the sequence.

## Suggestion methods
- `suggest_for_position(pos, category=None, limit=5)`
  - Empty sequence: returns first `limit` matches (category-filtered if provided).
  - `pos <= 0`: nearest to the first item.
  - `pos >= len(sequence)`: nearest to the last item.
  - Between two items: minimizes distance to both neighbors.
  - Scoring: `distance / rating` (rating floored to 1); excludes IDs already in the sequence.
  - Category filtering uses `Categories LIKE` (adjust code if you rely on `cat_*` columns).
- `suggest_around(lat, lon, limit=5, category=None)`
  - Finds nearby places around a coordinate; scoring is `distance / rating`; category via `Categories LIKE`.

## Random category helper
- `get_suggest_category()`: Returns a random category from a preset list.

## Quick smoke test
Run directly:
```
python ChatSystem/location_sequence.py
```
This executes a sample `search_by_name` and a `suggest_for_position` run, printing IDs, names, and scores.

## Notes and caveats
- Missing/invalid coordinates skip a candidate silently.
- If your schema uses `cat_*` columns instead of `Categories` text, add a text `Categories` column or extend the queries to OR on `cat_<category> > 0`.
- Sequence is not automatically mutated by suggestion methods; they return IDs for the caller to append.
