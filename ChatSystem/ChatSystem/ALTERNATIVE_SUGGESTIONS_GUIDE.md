# Alternative Topic Suggestions Feature

## Overview

Enhanced the chatbot to suggest **both direct answers AND alternative topic-switching questions** based on missing information in `collected_information`. This allows users to either answer the current question or explore other aspects of trip planning.

## Key Features

### 1. Smart Alternative Generation
- Analyzes `collected_information` to identify missing fields
- Generates relevant questions for each missing field
- Combines with general exploration questions

### 2. Enhanced Suggestion Structure

**Before:**
```python
Suggestions: ["Direct Answer 1", "Direct Answer 2", "Direct Answer 3"]
```

**After:**
```python
Suggestions: [
    # Direct answers (first 3)
    "Direct Answer 1",
    "Direct Answer 2", 
    "Direct Answer 3",
    # Alternative topics (last 1-2)
    "What's my budget?",
    "How many days do I have?"
]
```

### 3. Context-Aware Alternatives

The system intelligently suggests alternatives based on what's missing:

| Missing Information | Alternative Suggestions |
|---------------------|------------------------|
| `start_location` | "Where should I start from?" |
| `categories` | "What type of places interest me?" |
| `destinations` | "Which attractions should I visit?" |
| `budget` | "What's my budget?" |
| `duration_days` | "How many days do I have?" |

Plus general alternatives:
- "Tell me about popular attractions"
- "Suggest me some categories"
- "What are the best places to visit?"
- "Help me plan a complete trip"

## Implementation

### New Methods in `ChatBox.py`

#### 1. `_generate_alternative_suggestions(num_suggestions=2)`
```python
def _generate_alternative_suggestions(self, num_suggestions=2) -> list:
    """Generate alternative questions based on missing information."""
    # Maps missing fields to questions
    # Returns list of alternative questions
```

**Logic:**
1. Check which fields in `collected_information` are `None`
2. Map each missing field to a user-friendly question
3. Add general exploration questions
4. Randomly select up to `num_suggestions` alternatives

#### 2. `_enhance_suggestions_with_alternatives(base_suggestions, num_alternatives=1)`
```python
def _enhance_suggestions_with_alternatives(self, base_suggestions, num_alternatives=1):
    """Enhance base suggestions by adding alternative topic-switching suggestions."""
    # Combines base suggestions (max 3) with alternatives
    # Returns max 5 suggestions total
```

**Logic:**
1. Take first 3 base suggestions (direct answers)
2. Add 1-2 alternative questions
3. Limit total to 5 suggestions to avoid overwhelming users

### Updated Response Flow

Every bot response now includes alternatives:

```python
# Example: confirm_start_location
response = Bot_ask_category(location_sequence=self.location_sequence)
response.suggestions = self._enhance_suggestions_with_alternatives(
    response.suggestions, 
    num_alternatives=2
)
return response
```

## Usage Example

### Conversation Flow

```
🤖 Bot: "Where do you start your journey from?"

💡 Suggestions:
   📝 Direct Answers:
      1. Ho Chi Minh City
      2. Hanoi
      3. Da Nang
   🔄 Or Ask About:
      4. What type of places interest me?
      5. Which attractions should I visit?

👤 User: "Ho Chi Minh City" (answers directly)
    OR
👤 User: "Which attractions should I visit?" (switches topic)
```

### Dynamic Adaptation

As information is collected, alternatives adapt:

**Early in conversation (many fields missing):**
```
Alternatives: 
  - "What type of places interest me?"
  - "Which attractions should I visit?"
```

**Late in conversation (few fields missing):**
```
Alternatives:
  - "How many days do I have?"
  - "What are the best places to visit?"
```

## Benefits

### 1. **User Flexibility**
- Users aren't forced to answer questions in strict order
- Can explore topics that interest them most

### 2. **Natural Conversation**
- Feels less like a form, more like a conversation
- Users can change direction naturally

### 3. **Discovery**
- Users discover questions they might not have thought to ask
- Encourages exploration of all trip planning aspects

### 4. **Reduced Friction**
- If user doesn't know an answer, they can switch to something they do know
- Prevents conversation stalling

## Configuration

### Adjust Number of Alternatives

Change in method calls throughout `_computeResponse_from_user_input`:

```python
# More alternatives (up to 2)
response.suggestions = self._enhance_suggestions_with_alternatives(
    response.suggestions, 
    num_alternatives=2
)

# Fewer alternatives (just 1)
response.suggestions = self._enhance_suggestions_with_alternatives(
    response.suggestions, 
    num_alternatives=1
)
```

### Customize Alternative Questions

Edit the `field_to_question` mapping in `_generate_alternative_suggestions`:

```python
field_to_question = {
    'start_location': "Where should I start from?",
    'categories': "What types of places do you recommend?",  # Customized
    'destinations': "Show me popular attractions",           # Customized
    'budget': "What budget levels do you support?",          # Customized
    'duration_days': "How long should my trip be?"           # Customized
}
```

### Add More General Alternatives

Edit `general_alternatives` list:

```python
general_alternatives = [
    "Tell me about popular attractions",
    "Suggest me some categories",
    "What are the best places to visit?",
    "Help me plan a complete trip",
    "What's the weather like?",           # Add new
    "Tell me about local cuisine",        # Add new
    "What's the best time to visit?"      # Add new
]
```

## Testing

### Run Automated Demo
```bash
cd ChatSystem
python test_alternative_suggestions.py --mode demo
```

### Run Interactive Demo
```bash
cd ChatSystem
python test_alternative_suggestions.py --mode interactive
```

### Expected Output
```
🤖 Bot: Where do you start your journey from?

💡 Suggestions:
  📝 Direct Answers:
     1. Ho Chi Minh City
     2. Hanoi
     3. Da Nang
  🔄 Or Ask About:
     4. What type of places interest me?
     5. Which attractions should I visit?

📊 Current collected info: {...}
   Missing: categories, destinations, budget, duration_days
```

## Frontend Integration

### Rendering Suggestions

```javascript
function renderSuggestions(suggestions) {
    const container = document.getElementById('suggestions');
    container.innerHTML = '';
    
    // First 3 are direct answers
    const directAnswers = suggestions.slice(0, 3);
    const alternatives = suggestions.slice(3);
    
    // Render direct answers
    if (directAnswers.length > 0) {
        const directSection = document.createElement('div');
        directSection.className = 'direct-suggestions';
        directSection.innerHTML = '<h4>📝 Quick Answers</h4>';
        
        directAnswers.forEach(suggestion => {
            const btn = createSuggestionButton(suggestion, 'direct');
            directSection.appendChild(btn);
        });
        
        container.appendChild(directSection);
    }
    
    // Render alternatives
    if (alternatives.length > 0) {
        const altSection = document.createElement('div');
        altSection.className = 'alternative-suggestions';
        altSection.innerHTML = '<h4>🔄 Or Ask About</h4>';
        
        alternatives.forEach(suggestion => {
            const btn = createSuggestionButton(suggestion, 'alternative');
            altSection.appendChild(btn);
        });
        
        container.appendChild(altSection);
    }
}

function createSuggestionButton(text, type) {
    const btn = document.createElement('button');
    btn.className = `suggestion-btn ${type}`;
    btn.textContent = text;
    btn.onclick = () => sendMessage(text);
    return btn;
}
```

### CSS Styling

```css
.direct-suggestions {
    margin-bottom: 15px;
}

.alternative-suggestions {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px dashed #ccc;
}

.suggestion-btn.direct {
    background: #4CAF50;
    color: white;
}

.suggestion-btn.alternative {
    background: #2196F3;
    color: white;
}

.suggestion-btn {
    margin: 4px;
    padding: 8px 16px;
    border: none;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s;
}

.suggestion-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
```

## Edge Cases Handled

1. **No Missing Information**: Falls back to general alternatives
2. **Many Missing Fields**: Randomly selects to avoid overwhelming user
3. **Maximum Suggestions**: Limited to 5 total (3 direct + 2 alternative)
4. **Empty Alternatives**: Gracefully handles with general questions

## Performance Considerations

- Alternative generation is fast (simple dictionary lookup + random sampling)
- No additional API calls required
- Minimal memory overhead

## Future Enhancements

1. **Prioritize Alternatives**: Weight alternatives by importance/dependency
2. **User History**: Learn which alternatives users click most
3. **Contextual Alternatives**: More sophisticated context analysis
4. **Multi-language**: Translate alternative questions
5. **Personalization**: Adapt alternatives to user preferences

---

**Implementation Date**: December 13, 2025  
**Status**: ✅ Complete and Ready for Testing
