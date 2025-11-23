from flask import Flask, request, jsonify
from journey_planner import path
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Python Service is Running!"

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'input' not in data:
        return jsonify({'error': 'No input provided'}), 400
    
    user_input = data['input']

    try:
        # Gọi hàm xử lý
        result = path(user_input)
        
        # Kiểm tra nếu kết quả trả về có lỗi từ bên trong hàm path
        if isinstance(result, dict) and "error" in result:
             return jsonify(result), 500

        return jsonify(result)

    except Exception as e:
        # Log lỗi ra terminal để debug
        print(f"Error detected: {e}")
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500
    
if __name__ == '__main__':
    app.run(port=5000)