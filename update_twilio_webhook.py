#!/usr/bin/env python3
"""
Update Twilio webhook to point to the new AI Receptionist v2
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_twilio_webhook():
    """Update Twilio phone number webhook to new v2 endpoint"""
    
    # Get Twilio credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN') 
    phone_number = os.getenv('TWILIO_PHONE_NUMBER', '+18287840392')  # Default from old config
    
    if not account_sid or not auth_token:
        print("❌ Error: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in .env file")
        print("💡 Add these to your .env file:")
        print("   TWILIO_ACCOUNT_SID=your_account_sid_here")
        print("   TWILIO_AUTH_TOKEN=your_auth_token_here")
        print("   TWILIO_PHONE_NUMBER=your_phone_number_here")
        return False
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        print(f"🔗 Connecting to Twilio account: {account_sid[:8]}...")
        
        # New webhook URLs
        webhook_url = "https://adaphone-v2.mindgen.app/api/voice/webhook"
        fallback_url = "https://adaphone-v2.mindgen.app/api/voice/no-answer"
        
        # Find the phone number
        phone_numbers = client.incoming_phone_numbers.list()
        target_number = None
        
        for number in phone_numbers:
            if number.phone_number == phone_number:
                target_number = number
                break
        
        if not target_number:
            print(f"❌ Error: Phone number {phone_number} not found in your Twilio account")
            print("📞 Available numbers:")
            for number in phone_numbers:
                print(f"   - {number.phone_number} ({number.friendly_name})")
            return False
        
        print(f"📞 Found phone number: {target_number.phone_number}")
        print(f"🔧 Current webhook: {target_number.voice_url}")
        
        # Update the webhook
        print(f"🚀 Updating webhook to: {webhook_url}")
        
        target_number.update(
            voice_url=webhook_url,
            voice_method='POST',
            voice_fallback_url=fallback_url,
            voice_fallback_method='POST'
        )
        
        print("✅ Webhook updated successfully!")
        print(f"📞 Phone number: {target_number.phone_number}")
        print(f"🎯 Voice webhook: {target_number.voice_url}")
        print(f"🔄 Fallback webhook: {target_number.voice_fallback_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating webhook: {e}")
        return False

def test_webhook():
    """Test the webhook endpoint"""
    import requests
    
    webhook_url = "https://adaphone-v2.mindgen.app/api/voice/webhook"
    test_data = {
        'CallSid': 'test_call_sid',
        'From': '+32123456789',
        'To': '+18287840392'
    }
    
    try:
        print(f"🧪 Testing webhook: {webhook_url}")
        response = requests.post(webhook_url, data=test_data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Webhook is responding correctly!")
            print(f"📋 Response: {response.text[:200]}...")
        else:
            print(f"⚠️ Webhook returned status: {response.status_code}")
            print(f"📋 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")

if __name__ == "__main__":
    print("🎯 L'Osteria AI Receptionist v2 - Twilio Webhook Update")
    print("=" * 60)
    
    # Update webhook
    success = update_twilio_webhook()
    
    if success:
        print("\n🧪 Testing webhook...")
        test_webhook()
        
        print("\n🎉 Setup Complete!")
        print("📞 Your Twilio phone number now points to AI Receptionist v2")
        print("🌐 Test at: https://adaphone-v2.mindgen.app/")
        print("📊 Status: https://adaphone-v2.mindgen.app/api/status")
    else:
        print("\n❌ Setup failed - please check your configuration")