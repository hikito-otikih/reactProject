# Quick Start: Proactive Chatbot with Suggestions

## 🚀 Quick Setup

### 1. Run the Example
```bash
cd ChatSystem
python example_proactive_chat.py --mode interactive
```

### 2. Observe the Flow
```
🤖 Bot: "Let's have a trip, tell me where to begin!"
💡 Suggestions:
   1. Ho Chi Minh City
   2. Hanoi
   3. Da Nang

👤 You: [Type or click suggestion]

🤖 Bot: "What type of place are you interested in?"
💡 Suggestions:
   1. Museums & Culture
   2. Parks & Nature
   3. Restaurants & Cafes
```

---

## 📋 Integration Checklist

### Backend (Already Complete ✅)
- [x] BotResponse classes have suggestions attribute
- [x] ChatBox supports proactive initiation
- [x] Dynamic suggestion generation via LLM
- [x] Static suggestions for standard questions

### Frontend (Your Next Steps)
- [ ] Add `/api/chat/start` endpoint that calls `chat_box.start_conversation()`
- [ ] Update response rendering to show suggestions
- [ ] Add click handlers for suggestion buttons
- [ ] Style suggestion UI components

---

## 💻 Frontend Code Template

### API Integration
```javascript
// Start conversation proactively
async function startChat() {
    const response = await fetch('/api/chat/start', {
        method: 'POST'
    });
    const data = await response.json();
    
    displayBotMessage(data.message, data.suggestions);
}

// Send user message
async function sendMessage(userMessage) {
    const response = await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
    });
    const data = await response.json();
    
    displayBotMessage(data.message, data.suggestions);
}
```

### UI Component
```javascript
function displayBotMessage(message, suggestions) {
    // Display message
    addMessageToChat(message, 'bot');
    
    // Display suggestions
    const suggestionsContainer = document.getElementById('suggestions');
    suggestionsContainer.innerHTML = '';
    
    suggestions.forEach(suggestion => {
        const btn = document.createElement('button');
        btn.className = 'suggestion-btn';
        btn.textContent = suggestion;
        btn.onclick = () => {
            sendMessage(suggestion);
            // Optionally show as user message
            addMessageToChat(suggestion, 'user');
        };
        suggestionsContainer.appendChild(btn);
    });
}
```

### CSS Styling
```css
.suggestion-btn {
    background: #f0f0f0;
    border: 1px solid #ddd;
    border-radius: 20px;
    padding: 8px 16px;
    margin: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.suggestion-btn:hover {
    background: #e0e0e0;
    transform: translateY(-2px);
}

#suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 10px 0;
}
```

---

## 🔌 Backend API Endpoint

### Express.js Example
```javascript
// Start conversation endpoint
app.post('/api/chat/start', async (req, res) => {
    const chatBox = new ChatBox(locationSequence);
    const initialResponse = chatBox.start_conversation();
    
    res.json({
        message: initialResponse.get_message(),
        suggestions: initialResponse.get_suggestions(),
        whom: 'bot'
    });
});

// Message handling endpoint
app.post('/api/chat/message', async (req, res) => {
    const { message } = req.body;
    const botResponse = chatBox.process_input(message);
    
    res.json({
        message: botResponse.get_message(),
        suggestions: botResponse.get_suggestions(),
        whom: 'bot',
        db_attraction: botResponse.db_attraction || [],
        suggested_attractions: botResponse.suggested_attractions || []
    });
});
```

### Python Flask Example
```python
from flask import Flask, request, jsonify
from ChatSystem.ChatBox import ChatBox
from ChatSystem.location_sequence import LocationSequence

app = Flask(__name__)
chat_boxes = {}  # Store chat sessions by session_id

@app.route('/api/chat/start', methods=['POST'])
def start_chat():
    session_id = request.json.get('session_id', 'default')
    
    location_seq = LocationSequence()
    chat_box = ChatBox(location_sequence=location_seq)
    chat_boxes[session_id] = chat_box
    
    initial_response = chat_box.start_conversation()
    
    return jsonify({
        'message': initial_response.get_message(),
        'suggestions': initial_response.get_suggestions(),
        'whom': 'bot'
    })

@app.route('/api/chat/message', methods=['POST'])
def send_message():
    session_id = request.json.get('session_id', 'default')
    message = request.json.get('message')
    
    chat_box = chat_boxes.get(session_id)
    if not chat_box:
        return jsonify({'error': 'Session not found'}), 404
    
    bot_response = chat_box.process_input(message)
    
    return jsonify({
        'message': bot_response.get_message(),
        'suggestions': bot_response.get_suggestions(),
        'whom': 'bot',
        'db_attraction': getattr(bot_response, 'db_attraction', []),
        'suggested_attractions': getattr(bot_response, 'suggested_attractions', [])
    })
```

---

## 🧪 Testing

### Manual Test (Terminal)
```bash
python ChatSystem/ChatBox.py
```

### Automated Test
```python
from ChatSystem.ChatBox import ChatBox
from ChatSystem.location_sequence import LocationSequence

# Initialize
chat_box = ChatBox(location_sequence=LocationSequence())

# Proactive start
response = chat_box.start_conversation()
print(f"Bot: {response.get_message()}")
print(f"Suggestions: {response.get_suggestions()}")

# User input
response = chat_box.process_input("Ho Chi Minh City")
print(f"Bot: {response.get_message()}")
print(f"Suggestions: {response.get_suggestions()}")
```

---

## 📊 Expected Behavior

### Conversation Start
```
✓ Bot asks first question automatically
✓ 3 suggestions provided
✓ No user input required to begin
```

### Each Turn
```
✓ User input processed (typed or clicked)
✓ Bot response with new question
✓ 3 relevant suggestions shown
✓ Suggestions are clickable
```

### Completion
```
✓ All required slots filled
✓ Itinerary generated
✓ Final suggestions for next actions
```

---

## 🔧 Customization

### Add More Suggestions
Edit `Response.py`:
```python
class Bot_ask_start_location(BotResponse):
    static_suggestions = [
        "Ho Chi Minh City",
        "Hanoi",
        "Da Nang",
        "Nha Trang",  # Add here
        "Hoi An"      # And here
    ]
```

### Change Proactive Question
Edit `ChatBox.py`:
```python
def start_conversation(self):
    if not self.conversation_started:
        self.conversation_started = True
        # Change this to any other question
        bot_response = Bot_ask_category(location_sequence=self.location_sequence)
        # ... rest of code
```

### Adjust Dynamic Suggestion Count
```python
suggestions = generate_dynamic_suggestions(
    context=context,
    question=question,
    num_suggestions=5  # Change from 3 to 5
)
```

---

## ❓ FAQ

**Q: Can users still type custom responses?**  
A: Yes! Suggestions are optional. Users can always type their own answers.

**Q: What if the LLM fails to generate suggestions?**  
A: Fallback suggestions are provided: ["Tell me more", "Skip this", "Continue"]

**Q: How do I disable proactive start?**  
A: Don't call `start_conversation()`. Just use `process_input()` directly.

**Q: Can I have different suggestions per language?**  
A: Yes! Detect language and switch `static_suggestions` lists accordingly.

**Q: How to track which suggestions users click?**  
A: Log the selected suggestion in your analytics when processing user input.

---

## 📞 Support

- **Full Documentation**: `PROACTIVE_SUGGESTIONS_GUIDE.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **Example Code**: `example_proactive_chat.py`
- **Source Files**: 
  - `ChatBox.py` - Main chatbot logic
  - `util/Response.py` - Response classes
  - `util/orchestrator.py` - Dynamic suggestions

---

**Last Updated**: December 12, 2025  
**Version**: 1.0  
**Status**: Production Ready ✅
