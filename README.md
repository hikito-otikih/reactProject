# Journey Planner

AI-powered journey planning system that converts natural language requests into optimized travel itineraries with real-time location data and intelligent path construction.

## Overview

The system processes user requests like *"Visit War Remnants Museum, have coffee at a cafe, then go to Ben Thanh Market"* and generates a complete journey plan with:
- Optimal destination selection based on ratings and proximity
- Realistic travel times and distances
- Operating hours validation
- Complete timeline with arrival/departure times

## Architecture

### 1. Information Extraction (`extract_info.py`)
**Purpose**: Parse natural language into structured journey requirements

**Input**: Natural language text
```
"Start from Landmark 81, visit 2 restaurants, then go to a bar"
```

**Output**: Structured JSON
```json
{
  "must_go_destinations": ["Landmark 81"],
  "must_go_categories": ["restaurant", "bar"],
  "journey_sequence": ["Landmark 81", "restaurant", "restaurant", "bar"],
  "number_of_destinations": 4,
  "journey_date": "2025-11-20",
  "start_time": "12:00"
}
```

**Technology**: Google Gemini 2.5 Flash API with prompt engineering for structured extraction

---

### 2. Candidate Graph Builder (`candidate_graph.py`)
**Purpose**: Find real-world location candidates for each journey requirement

**Process**:
1. **Geocode** anchor locations using Geoapify API
2. **Search** for category candidates using SerpAPI (Google Maps)
3. **Build graph** of possible destinations with metadata

**Output**: Candidate graph
```json
{
  "anchor_locations": [
    {"name": "Landmark 81", "lat": 10.7946, "lon": 106.7218, "order": 0}
  ],
  "category_candidates": {
    "restaurant": {
      "required_count": 2,
      "candidates": [
        {"name": "Nha Hang ABC", "rating": 4.5, "lat": 10.795, "lon": 106.722, ...}
      ]
    }
  }
}
```

**APIs**: Geoapify (geocoding), SerpAPI (place search)

---

### 3. Path Constructor (`path_constructor.py`)
**Purpose**: Select optimal destinations and construct timeline

**Algorithm**:
1. **Initialize** with anchor locations in order
2. **For each category**:
   - Score candidates: `score = rating / distance`
   - Filter by operating hours
   - Select top-rated nearby options
3. **Calculate timeline**:
   - Travel time via Geoapify routing API
   - Visit duration from category-based estimates
   - Cumulative arrival/departure times

**Output**: Optimized journey path
```json
{
  "path": [
    {
      "name": "Landmark 81",
      "arrival_time": "2025-11-20 12:00",
      "departure_time": "2025-11-20 12:30",
      "visit_duration_minutes": 30,
      "travel_time_minutes": 5,
      "distance_to_next_km": 1.2
    }
  ],
  "total_duration_minutes": 180,
  "total_distance_km": 5.4,
  "start_time": "2025-11-20 12:00",
  "end_time": "2025-11-20 15:00"
}
```

---

## Setup

### Requirements
```bash
pip install google-generativeai requests serpapi
```

### API Keys Required
- **Gemini API**: Natural language processing
- **SerpAPI**: Place search (Google Maps data)
- **Geoapify**: Geocoding and routing

### Configuration
Add your API keys to the respective files:
- `extract_info.py`: Gemini API key
- `candidate_graph.py`: SerpAPI and Geoapify keys
- `path_constructor.py`: Geoapify API key

---

## Usage

### Basic Usage
```python
from journey_planner import path

result = path("Visit 2 museums, have lunch at a restaurant, then go to a cafe")
```

### Run Tests
```bash
python journey_planner.py
```

### Output Format
```
📝 Input: Visit War Remnants Museum, then have coffee at a cafe
✓ Extracted: 1 destinations, 1 categories
✓ Found: 1 anchors, 12 candidates
✓ Path: 2 stops, 1h30m, 3.5km

🗺️  2025-11-20 14:00 → 2025-11-20 15:30
   1. War Remnants Museum (90m +15m)
   2. Cafe ABC (30m)
```

---

## Technical Details

### Scoring Algorithm
Destinations are scored using: **score = rating / distance**
- Higher ratings preferred for quality
- Closer locations preferred for efficiency
- Balanced approach for optimal experience

### Visit Duration Estimates
Category-based estimates (50+ categories):
- Museums: 90 minutes
- Restaurants: 60 minutes
- Cafes: 30 minutes
- Spas: 90 minutes
- Parks: 45 minutes
- Bars: 75 minutes

### Operating Hours Validation
- Checks if destinations are open at planned visit time
- Filters out closed locations
- Ensures realistic itineraries

### Travel Time Calculation
- Primary: Geoapify routing API (actual road distances)
- Fallback: Haversine formula (great circle distance)
- Accounts for real-world travel conditions

---

## Data Flow

```
User Input (Natural Language)
        ↓
    extract_info.py
        ↓
    Structured Requirements
        ↓
    candidate_graph.py
        ↓
    Graph of Candidates
        ↓
    path_constructor.py
        ↓
    Optimized Journey Path
```

---

## Default Behaviors

- **Journey Date**: Today if not specified
- **Start Time**: Current time + 2 hours if not specified
- **Number of Destinations**: 4 if not specified
- **Visit Order**: Preserved from user input
- **Category Multiplicity**: "Visit 3 museums" creates 3 museum stops

---

## Examples

### Example 1: Cultural Tour
**Input**: "Visit Ho Chi Minh City Museum, then 2 more museums, have lunch"

**Process**:
1. Extract: 1 specific museum + 2 category museums + 1 restaurant
2. Find candidates near the first museum
3. Select best-rated nearby museums and restaurant
4. Calculate optimal route and timeline

### Example 2: Food Tour
**Input**: "Start from Landmark 81, visit 2 restaurants for lunch and dinner"

**Process**:
1. Geocode Landmark 81
2. Find top-rated restaurants nearby
3. Schedule lunch (first restaurant) and dinner (second restaurant)
4. Calculate travel times between locations

---

## File Structure

```
v:\Engine\
├── extract_info.py         # NLP extraction using Gemini
├── candidate_graph.py      # Location search using SerpAPI
├── path_constructor.py     # Path optimization algorithm
├── journey_planner.py      # Main orchestrator
└── README.md              # This file
```

---

## Limitations

- Requires active internet for API calls
- Limited to locations with Google Maps data
- Operating hours may not always be current
- Travel times are estimates (traffic not considered)

---

## Future Enhancements

- User preference learning
- Multi-day journey planning
- Budget constraints
- Transportation mode selection
- Real-time traffic integration
- Collaborative trip planning
