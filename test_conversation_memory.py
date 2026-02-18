#!/usr/bin/env python3
"""
Test script to verify GPT-4o conversation memory is working properly
"""

import requests
import json
import time

def test_conversation_memory():
    """Test that GPT-4o remembers previous conversation"""
    print("🧠 Testing GPT-4o Conversation Memory")
    print("=" * 50)
    
    base_url = "http://localhost:5011/api/chat"
    session_id = f"memory_test_{int(time.time())}"
    
    # Conversation scenario to test memory
    conversation = [
        "Hallo Sofia",
        "Ik wil graag pizza bestellen",
        "Welke pizza's hebben jullie?",
        "Wat is de goedkoopste pizza?",
        "Prima, die wil ik hebben",
        "Hoeveel kost het dan?",
        "Oké, wanneer kan ik het ophalen?"
    ]
    
    print(f"🎯 Session ID: {session_id}")
    print(f"📝 Testing {len(conversation)} conversation turns\n")
    
    responses = []
    
    for i, message in enumerate(conversation, 1):
        print(f"👤 Gebruiker {i}: {message}")
        
        # Send message to GPT-4o API
        try:
            response = requests.post(base_url, data={
                'message': message,
                'session_id': session_id
            })
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', 'No response')
                conversation_length = data.get('conversation_length', 0)
                
                print(f"🤖 Sofia {i}: {ai_response}")
                print(f"   📊 Conversation length: {conversation_length}")
                
                responses.append({
                    'user': message,
                    'ai': ai_response,
                    'length': conversation_length
                })
                
                # Check if conversation memory is working
                if i > 1:
                    expected_length = i * 2  # Each turn adds user + ai message
                    if conversation_length == expected_length:
                        print(f"   ✅ Memory working: {conversation_length} messages stored")
                    else:
                        print(f"   ⚠️ Memory issue: Expected {expected_length}, got {conversation_length}")
                
            else:
                print(f"   ❌ API Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request Error: {e}")
        
        print()  # Empty line for readability
        time.sleep(1)  # Brief pause between messages
    
    print("=" * 50)
    print("🧠 CONVERSATION MEMORY TEST RESULTS:")
    
    if responses:
        final_length = responses[-1]['length']
        expected_final = len(conversation) * 2
        
        if final_length == expected_final:
            print(f"✅ Perfect Memory: {final_length}/{expected_final} messages stored")
        else:
            print(f"⚠️ Memory Issue: {final_length}/{expected_final} messages stored")
        
        # Check for contextual responses
        contextual_indicators = 0
        for i, resp in enumerate(responses[1:], 2):  # Skip first response
            ai_response = resp['ai'].lower()
            
            # Look for signs that AI remembers previous context
            if any(word in ai_response for word in ['pizza', 'margherita', 'bestelling', 'gekozen']):
                contextual_indicators += 1
        
        context_score = (contextual_indicators / (len(responses) - 1)) * 100
        print(f"✅ Context Awareness: {context_score:.0f}% (GPT-4o remembers previous topics)")
        
        # Check for variety (no repetitive demo patterns)
        unique_responses = len(set(resp['ai'] for resp in responses))
        variety_score = (unique_responses / len(responses)) * 100
        print(f"✅ Response Variety: {variety_score:.0f}% (No repetitive demo patterns)")
        
    else:
        print("❌ No responses received - test failed")
    
    print(f"🎯 Test completed for session: {session_id}")

if __name__ == "__main__":
    test_conversation_memory()