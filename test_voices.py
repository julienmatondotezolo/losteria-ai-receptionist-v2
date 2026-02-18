#!/usr/bin/env python3
"""
Voice Testing Script for L'Osteria AI Receptionist v2
Tests Cartesia multilingual voices in Dutch, French, and Italian
"""

import asyncio
import httpx
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")

class VoiceTester:
    """Test Cartesia voices in multiple languages"""
    
    def __init__(self):
        self.api_key = CARTESIA_API_KEY
        self.base_url = "https://api.cartesia.ai"
        self.test_results = []
    
    async def list_available_voices(self):
        """Get all available voices from Cartesia"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/voices",
                    headers={
                        "Cartesia-Version": "2024-06-10",
                        "X-API-Key": self.api_key
                    }
                )
                
                if response.status_code == 200:
                    voices = response.json()
                    print("🎭 Available Cartesia Voices:")
                    print("=" * 60)
                    for voice in voices:
                        print(f"📢 {voice.get('name', 'Unknown')}")
                        print(f"   ID: {voice.get('id')}")
                        print(f"   Language: {voice.get('language', 'N/A')}")
                        print(f"   Description: {voice.get('description', 'N/A')}")
                        print()
                    return voices
                else:
                    print(f"❌ Failed to get voices: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            print(f"❌ Error fetching voices: {e}")
            return []
    
    async def test_voice_sample(self, voice_id: str, voice_name: str, text: str, language: str):
        """Test a specific voice with sample text"""
        print(f"🎤 Testing {voice_name} ({language}): '{text}'")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/tts/bytes",
                    headers={
                        "Cartesia-Version": "2024-06-10",
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "model_id": "sonic-multilingual",
                        "transcript": text,
                        "voice": {
                            "mode": "id",
                            "id": voice_id
                        },
                        "output_format": {
                            "container": "wav",
                            "encoding": "pcm_s16le",
                            "sample_rate": 16000
                        },
                        "language": language
                    }
                )
                
                if response.status_code == 200:
                    # Save audio file for manual review
                    filename = f"test_{voice_name.lower().replace(' ', '_')}_{language}.wav"
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    
                    audio_size = len(response.content)
                    
                    result = {
                        "voice_name": voice_name,
                        "voice_id": voice_id,
                        "language": language,
                        "text": text,
                        "status": "✅ SUCCESS",
                        "audio_file": filename,
                        "audio_size": f"{audio_size} bytes",
                        "quality": "Manual review required"
                    }
                    
                    print(f"   ✅ Generated: {filename} ({audio_size} bytes)")
                    
                else:
                    result = {
                        "voice_name": voice_name,
                        "voice_id": voice_id, 
                        "language": language,
                        "text": text,
                        "status": f"❌ FAILED: {response.status_code}",
                        "error": response.text
                    }
                    
                    print(f"   ❌ Failed: {response.status_code} - {response.text}")
                
                self.test_results.append(result)
                
        except Exception as e:
            result = {
                "voice_name": voice_name,
                "voice_id": voice_id,
                "language": language, 
                "text": text,
                "status": "❌ ERROR",
                "error": str(e)
            }
            
            print(f"   ❌ Error: {e}")
            self.test_results.append(result)
    
    async def run_restaurant_voice_tests(self):
        """Test restaurant-specific phrases in multiple languages"""
        
        # Test phrases for L'Osteria
        test_phrases = [
            {
                "language": "nl",
                "text": "Goedemiddag, dit is L'Osteria Deerlijk. Waarmee kan ik u helpen?",
                "description": "Dutch/Flemish greeting"
            },
            {
                "language": "fr", 
                "text": "Bonjour, ici L'Osteria Deerlijk. Comment puis-je vous aider?",
                "description": "French greeting"
            },
            {
                "language": "it",
                "text": "Ciao! Benvenuti a L'Osteria Deerlijk. Come posso aiutarla?", 
                "description": "Italian greeting"
            },
            {
                "language": "nl",
                "text": "Voor reserveringen verbind ik u door met het restaurant. Een ogenblik alstublieft.",
                "description": "Dutch reservation transfer"
            },
            {
                "language": "fr",
                "text": "Pour les réservations, je vous mets en relation avec le restaurant. Un instant s'il vous plaît.",
                "description": "French reservation transfer"
            }
        ]
        
        # Test voices - focusing on multilingual options
        test_voices = [
            {
                "id": "a0e99841-438c-4a64-b679-ae501e7d6091", 
                "name": "Warm Female (Multilingual)",
                "description": "Current voice in code"
            },
            {
                "id": "79a125e8-cd45-4c13-8a67-188112f4dd22",
                "name": "Professional Female",
                "description": "Alternative option"
            }
        ]
        
        print("🧪 Testing L'Osteria Voice Quality")
        print("=" * 60)
        print(f"API Key: {'✅ Provided' if self.api_key else '❌ Missing'}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test each voice with each phrase
        for voice in test_voices:
            print(f"🎭 Testing Voice: {voice['name']}")
            print(f"   ID: {voice['id']}")
            print()
            
            for phrase in test_phrases:
                await self.test_voice_sample(
                    voice["id"],
                    voice["name"],
                    phrase["text"],
                    phrase["language"]
                )
                
                # Small delay between requests
                await asyncio.sleep(0.5)
            
            print()
    
    def generate_report(self):
        """Generate final test report"""
        print("📊 VOICE TESTING REPORT")
        print("=" * 60)
        
        # Group results by language
        by_language = {}
        for result in self.test_results:
            lang = result["language"]
            if lang not in by_language:
                by_language[lang] = []
            by_language[lang].append(result)
        
        # Report by language
        for lang, results in by_language.items():
            lang_name = {
                "nl": "🇳🇱 Dutch/Flemish",
                "fr": "🇫🇷 French", 
                "it": "🇮🇹 Italian"
            }.get(lang, f"🌍 {lang.upper()}")
            
            print(f"\n{lang_name}:")
            print("-" * 40)
            
            success_count = sum(1 for r in results if "SUCCESS" in r["status"])
            total_count = len(results)
            
            print(f"Success Rate: {success_count}/{total_count}")
            
            for result in results:
                if "SUCCESS" in result["status"]:
                    print(f"  ✅ {result['voice_name']}: {result['audio_file']}")
                else:
                    print(f"  ❌ {result['voice_name']}: {result.get('error', 'Failed')}")
        
        # Overall summary
        total_success = sum(1 for r in self.test_results if "SUCCESS" in r["status"])
        total_tests = len(self.test_results)
        
        print(f"\n📈 OVERALL RESULTS: {total_success}/{total_tests} successful")
        
        # Recommendation
        print(f"\n🎯 RECOMMENDATION:")
        if total_success == total_tests:
            print("✅ Cartesia sonic-multilingual handles all languages well!")
            print("   → Proceed with current Cartesia stack")
        elif total_success >= total_tests * 0.7:
            print("⚠️  Mixed results - some languages work better than others")
            print("   → Consider hybrid approach (Cartesia + ElevenLabs)")
        else:
            print("❌ Poor multilingual performance")
            print("   → Switch to ElevenLabs for better language support")
        
        print(f"\n💡 Next steps:")
        print("1. Listen to generated .wav files for quality assessment")
        print("2. Test with native Dutch/French speakers")
        print("3. Compare with ElevenLabs if quality is insufficient")
        
        return by_language

async def main():
    """Main testing function"""
    print("🎭 L'Osteria Voice Testing Suite")
    print("Testing Cartesia multilingual capabilities...")
    print()
    
    if not CARTESIA_API_KEY:
        print("❌ CARTESIA_API_KEY not found in .env file")
        print("Please add your API key and try again.")
        return
    
    tester = VoiceTester()
    
    # List available voices first
    print("🔍 Discovering available voices...")
    voices = await tester.list_available_voices()
    
    if not voices:
        print("❌ Could not retrieve voices. Check your API key.")
        return
    
    print("\n" + "="*60)
    input("Press Enter to start voice testing...")
    
    # Run restaurant-specific tests
    await tester.run_restaurant_voice_tests()
    
    # Generate final report
    tester.generate_report()
    
    print(f"\n🎧 Audio files generated in current directory")
    print("   → Play them to evaluate voice quality")
    print("   → Test with native Dutch/French speakers")

if __name__ == "__main__":
    asyncio.run(main())