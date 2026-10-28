import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

ANALYSIS_SYSTEM_PROMPT = """
You are an expert Senior Engineering Mentor. 
Analyze this student project report and return a concise technical briefing for Priya (the HR/Tech Lead interviewer).
Include:
1. Candidate Name & Project Title
2. Core Tech Stack (Frontend, Backend, DB, Cloud)
3. 3 Key Implementation Strengths
4. 3 Tough Technical Verification Questions to ask in the live review call.
Keep the briefing under 200 words.
"""

def analyze_project_report(file_path: str) -> str:
    """Uploads and analyzes the PDF using Gemini multimodal capabilities."""
    print(f"[+] Analyzing uploaded report: {file_path}")
    
    # Upload file to Gemini File API
    uploaded_file = client.files.upload(file=file_path)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            uploaded_file,
            "Provide the technical briefing and review questions for this project."
        ],
        config=types.GenerateContentConfig(
            system_instruction=ANALYSIS_SYSTEM_PROMPT,
            temperature=0.2
        )
    )
    
    briefing = response.text.strip()
    print("[+] Report briefing generated successfully.")
    return briefing