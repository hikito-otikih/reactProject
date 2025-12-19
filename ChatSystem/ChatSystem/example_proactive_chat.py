"""
Example: Proactive Chatbot with Smart Suggestions

This example demonstrates:
1. Proactive conversation initiation
2. Static suggestions for standard questions
3. Dynamic LLM-based suggestions for complex queries
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ChatSystem.ChatBox import ChatBox
from ChatSystem.location_sequence import LocationSequence


def print_separator():
    print("\n" + "=" * 60 + "\n")


def display_response(bot_response):
    """Display bot response with suggestions in a formatted way."""
    print(f"🤖 Bot: {bot_response.get_message()}")
    
    suggestions = bot_response.get_suggestions()
    if suggestions:
        print(f"\n💡 Quick Suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
    
    # Display any database results
    if hasattr(bot_response, 'db_attraction') and bot_response.db_attraction:
        print(f"\n🏛️  Attraction IDs: {bot_response.db_attraction}")
    
    if hasattr(bot_response, 'suggested_attractions') and bot_response.suggested_attractions:
        print(f"\n🎯 Suggested Attractions: {bot_response.suggested_attractions}")
    
    if hasattr(bot_response, 'listOfItinerary') and bot_response.listOfItinerary:
        print(f"\n📋 Itinerary: {bot_response.listOfItinerary}")


def simulate_conversation():
    """Simulate a conversation with the proactive chatbot."""
    
    print("╔" + "=" * 58 + "╗")
    print("║  PROACTIVE CHATBOT WITH SMART SUGGESTIONS DEMO          ║")
    print("╚" + "=" * 58 + "╝")
    
    # Initialize chatbot
    location_seq = LocationSequence()
    chat_box = ChatBox(location_sequence=location_seq)
    
    # PROACTIVE START: Bot initiates the conversation
    print_separator()
    print("🚀 Chatbot is starting the conversation proactively...")
    print_separator()
    
    initial_response = chat_box.start_conversation()
    if initial_response:
        display_response(initial_response)
    
    # Simulated conversation flow
    conversation_flow = [
        {
            "input": "Ho Chi Minh City",
            "description": "User selects first suggestion"
        },
        {
            "input": "Museums & Culture",
            "description": "User selects category suggestion"
        },
        {
            "input": "War Remnants Museum",
            "description": "User specifies destination"
        },
        {
            "input": "3 days, budget friendly, 5 attractions",
            "description": "User selects extra info suggestion"
        }
    ]
    
    print("\n" + "─" * 60)
    print("Starting simulated conversation...")
    print("─" * 60 + "\n")
    
    for turn in conversation_flow:
        print_separator()
        print(f"👤 User: {turn['input']}")
        print(f"   ({turn['description']})")
        print()
        
        bot_response = chat_box.process_input(turn['input'])
        display_response(bot_response)
    
    print_separator()
    print("✅ Conversation completed successfully!")
    print("\n📊 Collected Information:")
    print(f"   {chat_box.collected_information}")
    print_separator()


def interactive_mode():
    """Run in interactive mode for manual testing."""
    
    print("╔" + "=" * 58 + "╗")
    print("║  INTERACTIVE CHATBOT MODE                               ║")
    print("╚" + "=" * 58 + "╝")
    print("\n💡 Tips:")
    print("   - You can type freely or use the numbered suggestions")
    print("   - Type 'exit', 'quit', or 'bye' to end the conversation")
    print("   - The bot will start the conversation proactively\n")
    
    location_seq = LocationSequence()
    chat_box = ChatBox(location_sequence=location_seq)
    
    # Proactive start
    print_separator()
    initial_response = chat_box.start_conversation()
    if initial_response:
        display_response(initial_response)
    
    # Interactive loop
    while True:
        print_separator()
        user_input = input("👤 You: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\n👋 Goodbye! Thanks for chatting!")
            print_separator()
            break
        
        if not user_input:
            print("⚠️  Please enter a message")
            continue
        
        print()
        bot_response = chat_box.process_input(user_input)
        display_response(bot_response)
    
    print("\n📊 Final Collected Information:")
    print(f"   {chat_box.collected_information}")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Proactive Chatbot Demo')
    parser.add_argument(
        '--mode',
        choices=['simulate', 'interactive'],
        default='interactive',
        help='Run mode: simulate (auto demo) or interactive (manual)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'simulate':
        simulate_conversation()
    else:
        interactive_mode()
