from flask import Flask, request, jsonify
from ChatSystem.TOOL import TOOL
import logging
from deepdiff import DeepDiff
import pprint
import json

# Chat Scheme Example:
# {
#   "history": {
#     "responses": [
#       {
#         "whom": "bot",
#         "message": "Where does the fun begin today?",
#         "suggestions": [
#           "What type of places interest me?",
#           "Which attractions should I visit?"
#         ],
#         "database_results": []
#       },
#       {
#         "whom": "user",
#         "message": "ho chi minh ",
#         "suggestions": [],
#         "database_results": []
#       },
#       {
#         "whom": "bot",
#         "message": "Here are 3 catering recommendations in your area area.",
#         "suggestions": [
#           "Help me plan a complete trip",
#           "Which attractions should I visit?"
#         ],
#         "database_results": [
#           337,
#           252,
#           325
#         ]
#       }
#     ]
#   },
#   "start_coordinate": [
#     10.7628356,
#     106.6824824
#   ],
#   "sequence": [1,2,3]
# }


#TOOL reply scheme example:
#       {
#         "message": "Here are 3 catering recommendations in your area area.",
#         "suggestions": [
#           "Help me plan a complete trip",
#           "Which attractions should I visit?"
#         ],
#         "database_results": [
#           337,
#           252,
#           325
#         ]
#       }

app = Flask(__name__)

chat_demo = TOOL()

logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    logging.info("Home endpoint called")
    return "Hello"


def response_template(success, data=None, message=""):
    """Standard response template for all endpoints"""
    return jsonify({
        "success": success,
        "data": data,
        "message": message
    })


# ============ Location Sequence Endpoints ============

Query_without_chat_instance = TOOL()

@app.route('/api/search-by-name', methods=['GET'])
def search_by_name():
    """Search for locations by name"""
    try:
        data = request.args
        name = data.get('name')
        raw_exact = data.get('exact', 'true')
        exact = str(raw_exact).lower() == 'true'
        try:
            limit = int(data.get('limit', 10))
        except (ValueError, TypeError):
            limit = 10
        logging.info(f"Searching for name: {name}, exact: {exact}, limit: {limit}")
        # tool = get_or_create_tool(chat_id)
        results = Query_without_chat_instance.search_by_name(name, exact=exact, limit=limit)
        
        return response_template(True, data=results, 
                               message="Search completed")
    except Exception as e:
        return response_template(False, message=str(e))


@app.route('/api/get-suggest-category', methods=['GET'])
def get_suggest_category():
    """Get available suggestion categories"""
    try:
        history = request.args.get('history', {})
        if isinstance(history, str):
            history = json.loads(history)
        tool = TOOL()
        tool.load(history)
        # tool = TOOL("hisory"=history)
        # tool = chat_demo
        categories = tool.get_suggest_category()
        
        return response_template(True, data=categories, 
                               message="Categories retrieved")
    except Exception as e:
        return response_template(False, message=str(e))


@app.route('/api/suggest-for-position', methods=['GET'])
def suggest_for_position():
    """Get suggestions for a specific position in the sequence"""
    try:
        data = request.args
        try:
            position = int(data.get('position', -1))
        except (ValueError, TypeError):
            position = -1
        category = data.get('category') 
        try:
            limit = int(data.get('limit', 5))
        except (ValueError, TypeError):
            limit = 5
        history = data.get('history', {})
        if isinstance(history, str):
            history = json.loads(history)
        # # Thay thế dòng assert cũ bằng đoạn này:
        # diff = DeepDiff(history, history_example, ignore_order=True)

        # if diff:
        #     print("⚠️ PHÁT HIỆN KHÁC BIỆT:")
        #     pprint.pprint(diff, indent=2)
        #     # Dừng chương trình nếu muốn giống assert
        #     raise AssertionError("history does not match example")
        # else:
        #     print("✅ Hai object giống hệt nhau!")
        tool = TOOL()
        tool.load(history)
        #tool = chat_demo
        suggestions = tool.suggest_for_position(position=position, category=category, limit=limit)
        
        return response_template(True, data=suggestions, 
                               message="Suggestions retrieved")
    except Exception as e:
        return response_template(False, message=str(e))


@app.route('/api/suggest-around', methods=['GET'])
def suggest_around():
    """Get suggestions around specific coordinates"""
    try:
        data = request.args
        try:
            lat = float(data.get('lat'))
        except (ValueError, TypeError):
            lat = 10.0
        try:
            lon = float(data.get('lon'))
        except (ValueError, TypeError):
            lon = 100.0
        try:
            limit = int(data.get('limit', 10))
        except (ValueError, TypeError):
            limit = 10
        category = data.get('category')
        history = data.get('history', {})
        if isinstance(history, str):
            history = json.loads(history)
        
        tool = TOOL()
        tool.load(history)
        suggestions = tool.suggest_around(lat=lat, lon=lon, limit=limit, category=category)
        
        return response_template(True, data=suggestions, 
                               message="Suggestions retrieved")
    except Exception as e:
        return response_template(False, message=str(e))


@app.route('/api/suggest-itinerary-to-sequence', methods=['GET'])
def suggest_itinerary_to_sequence():
    """Get suggestions for completing the itinerary"""
    try:
        data = request.args
        try:
            limit = int(data.get('limit', 5))
        except (ValueError, TypeError):
            limit = 5
        history = data.get('history', {})
        if isinstance(history, str):
            history = json.loads(history)
        # tool = TOOL("hisory"=history)
        tool = TOOL()
        tool.load(history)
        suggestions = tool.suggest_itinerary_to_sequence(limit)
        
        return response_template(True, data=suggestions, 
                               message="Itinerary suggestions retrieved")
    except Exception as e:
        return response_template(False, message=str(e))


# ============ ChatBox Endpoints ============

@app.route('/api/process-input', methods=['POST'])
def process_input():
    """Process user input through the chatbox"""
    try:
        logging.info("process_input endpoint called")
        data = request.get_json()
        user_input = data.get('input')
        history = data.get('history', {})
        if isinstance(history, str):
            history = json.loads(history)
        tool = TOOL()
        tool.load(history)
        #tool = TOOL("hisory"=history)
        #response = tool.process_input(user_input)
        
        # response = {
        #     "message": "Here are 3 catering recommendations in your area area.",
        #     "suggestions": [
        #         "Help me plan a complete trip",
        #         "Which attractions should I visit?"
        #     ],
        #     "database_results": [
        #         337,
        #         252,
        #         325
        #     ]
        # }
        logging.info(f"Processing input: {user_input}")
        response = tool.process_input(user_input)
        logging.info("done processing input")
        logging.info(f"Processed input: {user_input}, Response: {response}")
        return response_template(True, data=response, 
                               message="Input processed successfully")
    except Exception as e:
        return response_template(False, message=str(e))


# ============ Health Check ============

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return response_template(True, data={"status": "healthy"}, message="Server is running")


# ============ Error Handlers ============

@app.errorhandler(404)
def not_found(error):
    return response_template(False, message="Endpoint not found"), 404


@app.errorhandler(500)
def internal_error(error):
    return response_template(False, message="Internal server error"), 500


history_example = {
  "history": {
    "responses": [
      {
        "whom": "user",
        "message": "hello",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Input processed successfully",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "user",
        "message": "hello",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "hello",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "ahihi",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "hello",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "Help me plan a complete trip",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "Which attractions should I visit?",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "Which attractions should I visit?",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "Which attractions should I visit?",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "hello",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "Help me plan a complete trip",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "Which attractions should I visit?",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "hello world",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      },
      {
        "whom": "user",
        "message": "hello quang",
        "suggestions": [],
        "database_results": []
      },
      {
        "whom": "bot",
        "message": "Here are 3 catering recommendations in your area area.",
        "suggestions": [
          "Help me plan a complete trip",
          "Which attractions should I visit?"
        ],
        "database_results": [
          337,
          252,
          325
        ]
      }
    ]
  },
  "start_coordinate": [
    10.766289296847185,
    106.66789054870605
  ],
  "sequence": [
    410,
    10,
    472,
    471
  ]
}

if __name__ == '__main__':
    chat_demo = TOOL()
    chat_demo.append(0, 1)
    chat_demo.append(1, 2)
    chat_demo.append(2, 3)    
    chat_demo.append(3, 4)    
    chat_demo.append(4, 5)    
    test = TOOL()
    test.load(history_example)
    app.run(debug=True, host='0.0.0.0', port=5000)
