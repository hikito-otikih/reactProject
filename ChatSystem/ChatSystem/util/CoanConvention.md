
Chat History: List of Dictionaries includes role and message, e.g.
[
  {"role": "user", "message": "Hello!"},
  {"role": "assistant", "message": "Hi there! How can I help you today?"}
]

Use function `process_user_input(user_input: str, chat_history: list[dict]) -> dict` to extract intent and parameters from user input.
    Parameters:
        user_input (str): User's message in any language
        conversation_history (list): Previous conversation context
            Format: [{'role': 'user'/'bot', 'message': 'text'}, ...]
    
    Returns:
        dict: {
            'function': 'function_name',
            'params': {...},
            'text': 'clarification_text' (only if asking for clarification)
        }