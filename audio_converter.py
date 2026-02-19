"""
Audio format converter for Twilio Media Streams to OpenAI Whisper
Converts mulaw (8kHz) to WAV format that Whisper can understand
"""
import base64
import audioop
import wave
import io
import tempfile
import os

class TwilioAudioConverter:
    def __init__(self):
        self.sample_rate = 8000  # Twilio's sample rate
        self.audio_buffer = []
        self.min_duration_ms = 1000  # Minimum 1 second of audio before transcription
        
    def add_audio_chunk(self, base64_payload):
        """Add a mulaw audio chunk from Twilio"""
        # Decode base64 to raw mulaw bytes
        mulaw_data = base64.b64decode(base64_payload)
        self.audio_buffer.append(mulaw_data)
        
    def should_transcribe(self):
        """Check if we have enough audio for transcription"""
        total_bytes = sum(len(chunk) for chunk in self.audio_buffer)
        # Each mulaw byte = 1 sample, 8000 samples/sec
        duration_ms = (total_bytes / self.sample_rate) * 1000
        return duration_ms >= self.min_duration_ms
        
    def convert_to_wav(self):
        """Convert buffered mulaw audio to WAV format for OpenAI Whisper"""
        if not self.audio_buffer:
            return None
            
        # Concatenate all audio chunks
        mulaw_data = b''.join(self.audio_buffer)
        
        # Convert mulaw to linear PCM (16-bit)
        linear_data = audioop.ulaw2lin(mulaw_data, 2)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)  # 8kHz
            wav_file.writeframes(linear_data)
        
        # Return WAV data
        wav_buffer.seek(0)
        wav_data = wav_buffer.read()
        
        # Clear buffer after conversion
        self.audio_buffer.clear()
        
        return wav_data
        
    def save_wav_for_whisper(self):
        """Create temporary WAV file for OpenAI Whisper API"""
        wav_data = self.convert_to_wav()
        if not wav_data:
            return None
            
        # Save to temporary file (OpenAI needs file path)
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_file.write(wav_data)
        temp_file.flush()
        temp_file.close()
        
        return temp_file.name
        
    def cleanup_temp_file(self, file_path):
        """Clean up temporary audio file"""
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"⚠️ Failed to cleanup temp file {file_path}: {e}")