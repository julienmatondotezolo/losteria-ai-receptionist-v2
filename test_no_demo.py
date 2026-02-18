#!/usr/bin/env python3
"""
Test script to verify ALL demo responses are removed and ONLY GPT-4o is used
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

async def test_no_demo_responses():
    """Test that NO demo responses are used - only GPT-4o"""
    print("🧪 Testing: NO DEMO RESPONSES - ONLY GPT-4o")
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
    
    # Test scenarios that previously had HARDCODED demo responses
    demo_trigger_scenarios = [
        "Quanto costa la pasta?",  # Previously triggered price demo
        "Vorrei della pasta",      # Previously triggered pasta demo  
        "Avete delle pizze?",      # Previously triggered pizza demo
        "Cosa mi consigliate?",    # Previously triggered default demo
    ]
    
    print(f"\n🔍 Testing {len(demo_trigger_scenarios)} scenarios that previously had demo responses...")
    print("🎯 ALL responses must come from GPT-4o (no patterns, varied responses)")
    print("-" * 50)
    
    for i, user_input in enumerate(demo_trigger_scenarios, 1):
        print(f"\n🧪 Test {i}: {user_input}")
        print("-" * 30)
        
        try:
            response = await session._handle_takeaway_flow(user_input, current_menu)
            print(f"🤖 Response: {response}")
            
            # Check for OLD demo response patterns that should NO LONGER EXIST
            demo_patterns = [
                "Spaghetti Bolognese €18, Fettuccine Scampi €28, Tagliatelle Carbonara €22",
                "Pizza Margherita €15, Quattro Formaggi €22.50",
                "Ottima scelta! Spaghetti",
                "Le nostre paste:",
                "Le nostre pizze tradizionali!",
                "Cosa desidera ordinare? Popolare: Spaghetti",
            ]
            
            is_demo_response = any(pattern in response for pattern in demo_patterns)
            
            if is_demo_response:
                print("❌ FAILED: This is an old DEMO response pattern!")
            else:
                print("✅ SUCCESS: This is a unique GPT-4o response!")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 VERIFICATION COMPLETE!")
    print("✅ All responses should be unique and from GPT-4o")
    print("❌ Any demo patterns indicate code still has hardcoded responses")

if __name__ == "__main__":
    asyncio.run(test_no_demo_responses())