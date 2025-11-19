from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Python Service is Running!"

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        text = data.get('text', '')

        word_count = len(text.split())
        processed_text = text.upper()

        return jsonify({
            'message': 'Processed successfully',
            'word_count': word_count,
            'result': processed_text
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)