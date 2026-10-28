import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # Switched to direct SSL (avoids connection drops)
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_APP_PASSWORD")

def send_performance_email(to_email: str, candidate_name: str, score_data: dict, feedback: str):
    """Sends an automated HTML evaluation scorecard via Gmail SMTP_SSL."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("[!] SENDER_EMAIL or SENDER_APP_PASSWORD missing in .env. Skipping email.")
        return

    # Clean any accidental spaces from copy-pasting the App Password
    clean_password = SENDER_PASSWORD.replace(" ", "").strip()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Performance & Code Review Evaluation: {candidate_name}"
    msg["From"] = f"Priya - Engineering HR <{SENDER_EMAIL}>"
    msg["To"] = to_email

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; background: #f8fafc; color: #1e293b; padding: 20px; }}
        .card {{ background: #ffffff; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0; max-width: 550px; margin: auto; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
        h2 {{ color: #0284c7; margin-bottom: 8px; }}
        .badge {{ background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px dashed #cbd5e1; }}
        .feedback {{ background: #f1f5f9; padding: 14px; border-radius: 6px; margin-top: 18px; font-style: italic; line-height: 1.5; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h2>Engineering Review Report Card</h2>
        <p>Candidate: <strong>{candidate_name}</strong> &nbsp;|&nbsp; Evaluator: <span class="badge">Priya (AI HR Lead)</span></p>
        
        <div class="metric"><span>Technical Architecture:</span> <strong>{score_data.get('architecture', '8/10')}</strong></div>
        <div class="metric"><span>Code Clarity & Quality:</span> <strong>{score_data.get('code_quality', '8/10')}</strong></div>
        <div class="metric"><span>Live Verbal Defense:</span> <strong>{score_data.get('communication', '9/10')}</strong></div>
        <div class="metric"><span>Final Review Status:</span> <strong style="color: #16a34a;">{score_data.get('verdict', 'PASSED')}</strong></div>

        <div class="feedback">
          <strong>Reviewer Feedback:</strong><br>
          {feedback}
        </div>
      </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, "html"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=15) as server:
            server.login(SENDER_EMAIL, clean_password)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print(f"[+] Review email sent successfully to {to_email}")
    except Exception as e:
        print(f"[!] Email dispatch error: {e}")