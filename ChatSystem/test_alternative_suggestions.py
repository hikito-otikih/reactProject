"""
Test script to demonstrate alternative suggestions feature
Shows how the bot suggests both direct answers AND alternative topic-switching questions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ChatSystem.ChatBox import ChatBox
from ChatSystem.location_sequence import LocationSequence


def print_separator():
    print("\n" + "=" * 70 + "\n")


def display_suggestions(suggestions, title="💡 Suggestions"):
    """Display suggestions in a formatted way, highlighting alternatives."""
    if not suggestions:
        return
    
    print(f"\n{title}:")
    
    # First 3 are usually direct answers, rest are alternatives
    direct_answers = suggestions[:3]
    alternatives = suggestions[3:]
    
    if direct_answers:
        print("  📝 Direct Answers:")
        for i, suggestion in enumerate(direct_answers, 1):
            print(f"     {i}. {suggestion}")
    
    if alternatives:
        print("  🔄 Or Ask About:")
        for i, suggestion in enumerate(alternatives, len(direct_answers) + 1):
            print(f"     {i}. {suggestion}")


def test_alternative_suggestions():
    """Test the alternative suggestions feature."""
    
    print("╔" + "=" * 68 + "╗")
    print("║  ALTERNATIVE SUGGESTIONS DEMO                                    ║")
    print("║  Bot suggests both direct answers AND topic-switching questions ║")
    print("╚" + "=" * 68 + "╝")
    
    location_seq = LocationSequence()
    chat_box = ChatBox(location_sequence=location_seq)
    
    # Test 1: Initial conversation
    print_separator()
    print("🚀 Test 1: Bot starts conversation proactively")
    print("-" * 70)
    
    initial = chat_box.start_conversation()
    print(f"🤖 Bot: {initial.get_message()}")
    display_suggestions(initial.get_suggestions())
    
    print("\n📊 Current collected info:", chat_box.collected_information)
    print("   Missing: categories, destinations, budget, duration_days")
    
    # Test 2: User provides start location
    print_separator()
    print("🚀 Test 2: User provides start location")
    print("-" * 70)
    print("👤 User: Ho Chi Minh City")
    
    response2 = chat_box.process_input("Ho Chi Minh City")
    print(f"\n🤖 Bot: {response2.get_message()}")
    display_suggestions(response2.get_suggestions())
    
    print("\n📊 Current collected info:", chat_box.collected_information)
    print("   Missing: categories, destinations, budget, duration_days")
    
    # Test 3: User switches topic using alternative suggestion
    print_separator()
    print("🚀 Test 3: User switches topic (asks about budget instead of answering category)")
    print("-" * 70)
    print("👤 User: What's my budget? (alternative topic)")
    
    response3 = chat_box.process_input("I have a budget of 500 USD")
    print(f"\n🤖 Bot: {response3.get_message()}")
    display_suggestions(response3.get_suggestions())
    
    print("\n📊 Current collected info:", chat_box.collected_information)
    
    # Test 4: User provides category
    print_separator()
    print("🚀 Test 4: User answers category question")
    print("-" * 70)
    print("👤 User: Museums & Culture")
    
    response4 = chat_box.process_input("Museums & Culture")
    print(f"\n🤖 Bot: {response4.get_message()}")
    display_suggestions(response4.get_suggestions())
    
    print("\n📊 Current collected info:", chat_box.collected_information)
    print("   Missing: destinations, duration_days")
    
    # Test 5: Show how alternatives change based on missing info
    print_separator()
    print("🚀 Test 5: Notice how alternatives adapt to missing information")
    print("-" * 70)
    print("👤 User: Ben Thanh Market")
    
    response5 = chat_box.process_input("Ben Thanh Market")
    print(f"\n🤖 Bot: {response5.get_message()}")
    display_suggestions(response5.get_suggestions())
    
    print("\n📊 Current collected info:", chat_box.collected_information)
    print("   Missing: duration_days")
    print("\n   ✅ Notice: Alternative suggestions now focus on remaining missing fields!")
    
    print_separator()


def interactive_demo():
    """Interactive demo showing alternative suggestions."""
    
    print("╔" + "=" * 68 + "╗")
    print("║  INTERACTIVE ALTERNATIVE SUGGESTIONS DEMO                       ║")
    print("╚" + "=" * 68 + "╝")
    
    print("\n💡 How it works:")
    print("   • Each bot response includes direct answer suggestions")
    print("   • PLUS alternative questions you can ask (based on missing info)")
    print("   • You can answer directly OR switch topics!")
    print("\n   Type 'exit' to quit\n")
    
    location_seq = LocationSequence()
    chat_box = ChatBox(location_sequence=location_seq)
    
    # Start conversation
    print_separator()
    initial = chat_box.start_conversation()
    print(f"🤖 Bot: {initial.get_message()}")
    display_suggestions(initial.get_suggestions())
    
    # Interactive loop
    turn = 1
    while True:
        print_separator()
        print(f"Turn {turn}:")
        user_input = input("👤 You: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\n👋 Goodbye!")
            break
        
        if not user_input:
            print("⚠️  Please enter a message")
            continue
        
        print()
        bot_response = chat_box.process_input(user_input)
        print(f"🤖 Bot: {bot_response.get_message()}")
        display_suggestions(bot_response.get_suggestions())
        
        # Show collected info
        missing = [k for k, v in chat_box.collected_information.items() if v is None]
        print(f"\n📊 Collected: {[k for k, v in chat_box.collected_information.items() if v is not None]}")
        if missing:
            print(f"   Missing: {missing}")
        
        turn += 1
    
    print("\n📋 Final collected information:")
    for key, value in chat_box.collected_information.items():
        print(f"   • {key}: {value}")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Alternative Suggestions Demo')
    parser.add_argument(
        '--mode',
        choices=['demo', 'interactive'],
        default='demo',
        help='Run mode: demo (automated) or interactive (manual)'
    )
    
    args = parser.parse_args()
    
    print("\n")
    if args.mode == 'demo':
        test_alternative_suggestions()
    else:
        interactive_demo()
    
    print("\n✅ Demo completed!\n")
