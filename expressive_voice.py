import os
import io
import sounddevice as sd
import soundfile as sf
import requests

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Warm, professional & conversational voice

def speak_human_emotion(text: str):
    """Converts text into ultra-realistic human speech with emotion and streams to GMeet mic."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.45,         # Lower stability = more expressive & emotional human inflections
            "similarity_boost": 0.85,
            "style": 0.35,
            "use_speaker_boost": True
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        audio_data, fs = sf.read(io.BytesIO(response.content), dtype='float32')
        
        # Virtual Cable Output vazhiya stream panrom
        devices = sd.query_devices()
        target_device = None
        for idx, dev in enumerate(devices):
            if "CABLE Input" in dev['name'] and dev['max_output_channels'] > 0:
                target_device = idx
                break
                
        sd.play(audio_data, fs, device=target_device)
        sd.wait()