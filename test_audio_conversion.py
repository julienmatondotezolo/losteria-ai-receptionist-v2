#!/usr/bin/env python3
"""
Test script for Twilio mulaw to WAV conversion
Validates that our audio converter can handle Twilio Media Streams format
"""

import base64
import tempfile
import os
from audio_converter import TwilioAudioConverter

def test_audio_conversion():
    """Test the audio conversion pipeline"""
    print("🧪 Testing Twilio mulaw to WAV conversion...")
    
    # Create converter
    converter = TwilioAudioConverter()
    
    # Generate test mulaw audio data (simulate Twilio payload)
    # This is a simple sine wave pattern in mulaw format
    import audioop
    import math
    
    # Generate 1 second of sine wave at 440Hz
    sample_rate = 8000
    duration = 1.0
    frequency = 440
    
    # Create linear PCM samples
    samples = []
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        sample = int(32767 * math.sin(2 * math.pi * frequency * t))
        samples.append(sample)
    
    # Convert to bytes
    linear_data = b''.join(sample.to_bytes(2, 'little', signed=True) for sample in samples)
    
    # Convert to mulaw
    mulaw_data = audioop.lin2ulaw(linear_data, 2)
    
    # Encode to base64 (as Twilio would send)
    base64_payload = base64.b64encode(mulaw_data).decode('utf-8')
    
    print(f"✅ Generated {len(mulaw_data)} bytes of mulaw test data")
    print(f"✅ Base64 payload length: {len(base64_payload)} chars")
    
    # Add chunks to converter (simulate multiple Twilio messages)
    chunk_size = 160  # Typical Twilio chunk size (20ms at 8kHz)
    chunks_added = 0
    
    for i in range(0, len(base64_payload), chunk_size * 4):  # *4 for base64 overhead
        chunk = base64_payload[i:i + chunk_size * 4]
        if chunk:
            converter.add_audio_chunk(chunk)
            chunks_added += 1
    
    print(f"✅ Added {chunks_added} audio chunks")
    
    # Check if ready for transcription
    if converter.should_transcribe():
        print("✅ Converter says audio is ready for transcription")
        
        # Convert to WAV
        wav_file = converter.save_wav_for_whisper()
        
        if wav_file and os.path.exists(wav_file):
            file_size = os.path.getsize(wav_file)
            print(f"✅ WAV file created: {wav_file} ({file_size} bytes)")
            
            # Verify WAV file header
            with open(wav_file, 'rb') as f:
                header = f.read(12)
                if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                    print("✅ Valid WAV file format detected")
                else:
                    print("❌ Invalid WAV file format")
            
            # Cleanup
            converter.cleanup_temp_file(wav_file)
            if not os.path.exists(wav_file):
                print("✅ Temporary file cleaned up successfully")
            else:
                print("⚠️ Temporary file cleanup failed")
        else:
            print("❌ Failed to create WAV file")
    else:
        print("❌ Converter says not enough audio for transcription")
    
    print("🧪 Audio conversion test completed")

if __name__ == "__main__":
    test_audio_conversion()