"""
Prompt Configuration Module
Contains domain mappings, keywords, schemas, and few-shot examples for dynamic prompt building.
"""

# ============================================================================
# DOMAIN KEYWORD MAPPINGS
# ============================================================================
DOMAIN_KEYWORDS = {
    'accommodation': {
        'hotel', 'room', 'resort', 'stay', 'accommodation', 'hostel', 'motel',
        'check-in', 'check-out', 'booking', 'suite', 'lodge', 'inn', 'guesthouse'
    },
    'transport': {
        'flight', 'fly', 'plane', 'airport', 'airline', 'seat', 'ticket',
        'depart', 'arrival', 'boarding', 'layover', 'class', 'economy', 'business',
        'train', 'bus', 'car', 'rental', 'taxi', 'uber'
    },
    'itinerary': {
        'trip', 'itinerary', 'tour', 'visit', 'plan', 'journey', 'explore',
        'travel', 'vacation', 'holiday', 'destination', 'attractions', 'sightseeing',
        'museum', 'park', 'restaurant', 'cafe', 'landmark', 'activities'
    },
    'modification': {
        'change', 'modify', 'update', 'no', 'not', 'different', 'another',
        'cheaper', 'expensive', 'better', 'worse', 'earlier', 'later',
        'next', 'previous', 'instead', 'replace', 'cancel', 'switch'
    },
    'general': {
        'hello', 'hi', 'help', 'thanks', 'bye', 'goodbye', 'what', 'how',
        'where', 'when', 'why', 'info', 'information', 'tell', 'show'
    }
}

# ============================================================================
# MODIFIER KEYWORDS (for context detection)
# ============================================================================
MODIFIER_KEYWORDS = {
    'change', 'no', 'not', 'modify', 'update', 'different', 'another',
    'cheaper', 'expensive', 'better', 'earlier', 'later', 'next', 'instead',
    'replace', 'cancel', 'switch', 'remove', 'add'
}

# ============================================================================
# VAGUE KEYWORDS (for ambiguity detection)
# ============================================================================
VAGUE_LOCATION_KEYWORDS = {
    'around me', 'nearby', 'near me', 'my location', 'here', 'around here',
    'close by', 'in the area', 'local'
}

VAGUE_CATEGORY_KEYWORDS = {
    'things to do', 'fun stuff', 'activities', 'recommendations', 
    'places to go', 'what to do', 'suggestions', 'options'
}

# ============================================================================
# FEW-SHOT EXAMPLES BY DOMAIN
# ============================================================================
FEW_SHOT_EXAMPLES = {
    'accommodation': [
        {
            'input': 'Book a 5-star hotel in Paris for 3 nights',
            'output': {
                'intents': [{
                    'intent': 'book_hotel',
                    'suggested_function': 'book_hotel',
                    'confidence': 0.5,
                    'slots': {
                        'destination': 'Paris',
                        'accommodation_type': '5-star hotel',
                        'duration_nights': 3,
                        'budget': None,
                        'preferences': []
                    },
                    'entities': [
                        {'type': 'LOCATION', 'text': 'Paris'},
                        {'type': 'NUMBER', 'text': '5-star'},
                        {'type': 'NUMBER', 'text': '3 nights'}
                    ],
                    'keywords': ['book', 'hotel', 'Paris', '5-star', 'nights']
                }],
                'followup': False,
                'clarify_text': None
            }
        },
        {
            'input': 'Need a cheap hostel near the beach',
            'output': {
                'intents': [{
                    'intent': 'search_accommodation',
                    'suggested_function': 'search_hotels',
                    'confidence': 0.5,
                    'slots': {
                        'destination': None,
                        'accommodation_type': 'hostel',
                        'budget': 'cheap',
                        'preferences': ['near beach']
                    },
                    'entities': [
                        {'type': 'PREFERENCES', 'text': 'cheap'},
                        {'type': 'PREFERENCES', 'text': 'near beach'}
                    ],
                    'keywords': ['cheap', 'hostel', 'beach', 'accommodation']
                }],
                'followup': True,
                'clarify_text': 'Which city or destination are you looking for?'
            }
        }
    ],
    'transport': [
        {
            'input': 'Book a business class flight to Tokyo on June 15th',
            'output': {
                'intents': [{
                    'intent': 'book_flight',
                    'suggested_function': 'book_flight',
                    'confidence': 0.5,
                    'slots': {
                        'destination': 'Tokyo',
                        'departure_date': '2025-06-15',
                        'seat_class': 'business',
                        'travelers': {'adults': 1, 'children': None, 'infants': None}
                    },
                    'entities': [
                        {'type': 'LOCATION', 'text': 'Tokyo'},
                        {'type': 'DATE', 'text': 'June 15th'},
                        {'type': 'PREFERENCES', 'text': 'business class'}
                    ],
                    'keywords': ['flight', 'Tokyo', 'business', 'June']
                }],
                'followup': False,
                'clarify_text': None
            }
        }
    ],
    'itinerary': [
        {
            'input': 'Plan a 3-day trip to Rome with museums and good restaurants',
            'output': {
                'intents': [{
                    'intent': 'create_itinerary',
                    'suggested_function': 'suggest_itinerary',
                    'confidence': 0.50,
                    'slots': {
                        'destination': 'Rome',
                        'duration_days': 3,
                        'categories': ['museum', 'restaurant'],
                        'preferences': ['museums', 'good restaurants']
                    },
                    'entities': [
                        {'type': 'LOCATION', 'text': 'Rome'},
                        {'type': 'NUMBER', 'text': '3-day'},
                        {'type': 'PREFERENCES', 'text': 'museums'},
                        {'type': 'PREFERENCES', 'text': 'good restaurants'}
                    ],
                    'keywords': ['trip', 'Rome', 'museums', 'restaurants', 'itinerary']
                }],
                'followup': False,
                'clarify_text': None
            }
        }
    ],
    'general': [
        {
            'input': 'Hello',
            'output': {
                'intents': [{
                    'intent': 'greeting',
                    'suggested_function': 'greet',
                    'confidence': 0.50,
                    'slots': {},
                    'entities': [],
                    'keywords': ['hello', 'greeting']
                }],
                'followup': False,
                'clarify_text': None
            }
        }
    ],
    'clarification': [
        {
            'input': 'What is there to do around here?',
            'output': {
                'intents': [{
                    'intent': 'ask_clarify',
                    'suggested_function': 'ask_clarify',
                    'confidence': 1.0,
                    'slots': {
                        'destination': 'current_location',
                        'category': None
                    },
                    'missing_info': ['category'],
                    'keywords': ['things to do', 'around here', 'nearby']
                }],
                'followup': True,
                'clarify_question': 'I can see you are looking for activities nearby. Are you interested in historical sites, food, or outdoor parks?'
            }
        },
        {
            'input': 'Show me things to do nearby',
            'output': {
                'intents': [{
                    'intent': 'ask_clarify',
                    'suggested_function': 'ask_clarify',
                    'confidence': 1.0,
                    'slots': {
                        'destination': 'current_location',
                        'category': None
                    },
                    'missing_info': ['category'],
                    'keywords': ['things to do', 'nearby']
                }],
                'followup': True,
                'clarify_question': 'What type of places are you interested in? For example: restaurants, museums, parks, shopping, or entertainment?'
            }
        }
    ]
}

# ============================================================================
# DOMAIN-SPECIFIC SCHEMA DEFINITIONS
# ============================================================================
SCHEMA_SLOTS = {
    'accommodation': {
        'destination': 'null',
        'start_date': 'null',
        'end_date': 'null',
        'duration_nights': 'null',
        'accommodation_type': 'null',
        'budget': 'null',
        'travelers': '{"adults":null,"children":null,"infants":null}',
        'preferences': '[]'
    },
    'transport': {
        'origin': 'null',
        'destination': 'null',
        'departure_date': 'null',
        'return_date': 'null',
        'seat_class': 'null',
        'travelers': '{"adults":null,"children":null,"infants":null}',
        'budget': 'null',
        'preferences': '[]'
    },
    'itinerary': {
        'destination': 'null',
        'categories': '[]',
        'start_location': 'null',
        'duration_days': 'null',
        'start_time': 'null',
        'budget': 'null',
        'preferences': '[]'
    },
    'general': {
        'query': 'null'
    }
}
