import os
import json
import edge_tts
from google import genai
from google.genai import types
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MENTOR_SYSTEM_INSTRUCTION = """
You are Alex, an empathetic, supportive, and sharp Senior Engineering Lead reviewing an intern's project progress.
Speak naturally like a mentor on a 1-on-1 call:
1. Acknowledge what they did well specifically.
2. Highlight 2-3 constructive architectural or code fixes.
3. Outline next milestones for the upcoming week.

Return ONLY a valid JSON object matching this structure:
{
  "spoken_feedback": "A conversational script (under 120 words) for Alex to speak directly to the student in natural spoken English.",
  "score": 85,
  "strengths": ["Clear modular layout", "Good database normalization"],
  "improvements": ["Missing input sanitization", "Need error boundaries in frontend"],
  "next_milestone": "Implement token refresh logic and wire up unit tests."
}
"""

async def analyze_project_submission(student_name: str, week_number: int, doc_bytes: bytes, mime_type: str) -> dict:
    prompt = f"Student Name: {student_name}\nInternship Stage: Week {week_number} Review"
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=doc_bytes, mime_type=mime_type),
            prompt
        ],
        config=types.GenerateContentConfig(
            system_instruction=MENTOR_SYSTEM_INSTRUCTION,
            response_mime_type="application/json"
        )
    )
    return json.loads(response.text)

async def generate_mentor_voice(text: str, output_path: str = "feedback.mp3") -> str:
    # en-US-BrianNeural or en-US-AndrewNeural gives a conversational, warm mentor tone
    voice = "en-US-BrianNeural"
    communicate = edge_tts.Communicate(text, voice, rate="+2%", pitch="-1Hz")
    await communicate.save(output_path)
    return output_path

def generate_pdf_report(review_data: dict, student_name: str, week_no: int, output_pdf: str = "review_report.pdf") -> str:
    doc = SimpleDocTemplate(output_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, leading=24, textColor="#1E3A8A")
    story.append(Paragraph(f"Intern Evaluation Report - Week {week_no}", title_style))
    story.append(Paragraph(f"Candidate: <b>{student_name}</b> | Score: <b>{review_data.get('score')}/100</b>", styles['Normal']))
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>Mentor Assessment Summary</b>", styles['Heading2']))
    story.append(Paragraph(review_data.get('spoken_feedback', ''), styles['BodyText']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Key Strengths</b>", styles['Heading3']))
    for item in review_data.get('strengths', []):
        story.append(Paragraph(f"• {item}", styles['BodyText']))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Areas for Improvement</b>", styles['Heading3']))
    for item in review_data.get('improvements', []):
        story.append(Paragraph(f"• {item}", styles['BodyText']))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Next Milestone</b>", styles['Heading3']))
    story.append(Paragraph(review_data.get('next_milestone', ''), styles['BodyText']))

    doc.build(story)
    return output_pdf