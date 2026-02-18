#!/usr/bin/env python3
"""
Test script to verify GPT-4o is being used in takeaway flow
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import CallSession, fetch_restaurant_menu, format_menu_for_ai
from fastapi import WebSocket

class MockWebSocket:
    """Mock WebSocket for testing"""
    async def send_text(self, message):
        print(f"📤 Mock WebSocket would send: {message[:100]}...")

async def test_gpt4o_takeaway_flow():
    """Test the takeaway conversation flow"""
    print("🧪 Testing GPT-4o Takeaway Flow")
    print("=" * 50)
    
    # Create a mock call session
    mock_websocket = MockWebSocket()
    session = CallSession("test_call_123", mock_websocket)
    
    # Simulate language selection and takeaway choice
    session.selected_language = "it"
    session.call_state = "takeaway"
    
    # Fetch menu data
    print("📋 Fetching menu data...")
    menu_data = await fetch_restaurant_menu()
    if menu_data:
        current_menu = format_menu_for_ai(menu_data)
        print(f"✅ Menu loaded: {len(current_menu)} characters")
    else:
        print("❌ Failed to load menu")
        return
    
    # Test various conversation scenarios
    test_scenarios = [
        "Ciao, cosa mi consigliate per pranzo?",
        "Vorrei una pizza, cosa avete?", 
        "Quanto costa la pasta?",
        "Avete qualcosa senza glutine?",
        "Quali sono i vostri piatti del giorno?"
    ]
    
    for i, user_input in enumerate(test_scenarios, 1):
        print(f"\n🔍 Test {i}: {user_input}")
        print("-" * 30)
        
        try:
            response = await session._handle_takeaway_flow(user_input, current_menu)
            print(f"🤖 Response: {response}")
            
            # Check if response looks like GPT-4o (varied, contextual) vs demo (fixed patterns)
            if any(fixed_phrase in response for fixed_phrase in [
                "Spaghetti Bolognese €18", "Pizza Margherita €15", 
                "Ottima scelta! Spaghetti", "Le nostre paste:"
            ]):
                print("⚠️  WARNING: This looks like a demo response!")
            else:
                print("✅ This looks like a GPT-4o response!")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_gpt4o_takeaway_flow())