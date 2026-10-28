import speech_recognition as sr
from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
recognizer = sr.Recognizer()

conversation_history = [
    {"role": "user", "parts": ["Start call as Priya HR"]}
]

def listen_and_reply_live():
    with sr.Microphone() as source:
        print("[+] Priya (HR) is listening to the student...")
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        
        while True:
            try:
                audio = recognizer.listen(source, phrase_time_limit=5)
                student_speech = recognizer.recognize_google(audio)
                print(f"[Student]: {student_speech}")
                
                # Gemini generate conversation with human emotion
                prompt = f"Student said: '{student_speech}'. Reply back casually and warmly as Priya HR."
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"system_instruction": HUMAN_HR_EMOTIONAL_PROMPT}
                )
                
                hr_reply = response.text.strip()
                print(f"[Priya HR]: {hr_reply}")
                
                # Speak out with emotional voice
                speak_human_emotion(hr_reply)
                
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"Error: {e}")