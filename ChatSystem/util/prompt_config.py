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
    'itinerary': [
        {
            'input': 'Create an itinerary through 6 locations',
            'output': {
                'intents': [{
                    'intent': 'itinerary_planning',
                    'suggested_function': 'itinerary_planning',
                    'confidence': 0.95,
                    'slots': {
                        'destination': None,
                        'categories': [],
                        'limit': 6
                    }
                }],
                'followup': False,
                'clarify_question': None
            }
        },
        {
            'input': 'Plan a 3-day trip to Rome with museums and good restaurants',
            'output': {
                'intents': [{
                    'intent': 'itinerary_planning',
                    'suggested_function': 'itinerary_planning',
                    'confidence': 0.90,
                    'slots': {
                        'destination': 'Rome',
                        'categories': ['museum', 'restaurant'],
                        'limit': 3
                    }
                }],
                'followup': False,
                'clarify_question': None
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
                        'categories': None,
                        'limit': None
                    },
                    'missing_info': ['categories'],
                    'keywords': ['things to do', 'nearby']
                }],
                'followup': True,
                'clarify_question': 'What type of places are you interested in? For example: restaurants, museums, parks, shopping, or entertainment?'
            }
        }
    ],
    'general': [
        {
            'input': 'Show me museums',
            'output': {
                'intents': [{
                    'intent': 'suggest_attractions',
                    'suggested_function': 'suggest_attractions',
                    'confidence': 0.90,
                    'slots': {
                        'destination': None,
                        'categories': ['museum'],
                        'limit': 5
                    }
                }],
                'followup': False,
                'clarify_question': None
            }
        },
        {
            'input': 'Tell me about Bến Thành Market',
            'output': {
                'intents': [{
                    'intent': 'search_by_name',
                    'suggested_function': 'search_by_name',
                    'confidence': 0.95,
                    'slots': {
                        'destination': 'Bến Thành Market',
                        'categories': [],
                        'limit': None
                    }
                }],
                'followup': False,
                'clarify_question': None
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
        'limit': 'null'
    },
    'general': {
        'destination': 'null',
        'categories': '[]',
        'limit': 'null'
    }
}