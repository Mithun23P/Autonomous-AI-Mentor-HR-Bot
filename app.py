import os
import json
import shutil
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()
UPLOAD_DIR = "./uploaded_reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
BRIEFING_FILE = "./current_briefing.json"

REPORT_ANALYSIS_PROMPT = """
You are Priya, a Senior Engineering Mentor and HR Lead.
Analyze this submitted student project report and create a briefing for yourself to use in the live Google Meet call.

Extract and structure:
1. Candidate Name & Project Title
2. Core Architecture & Tech Stack (Frontend, Backend, Database, APIs)
3. Strong Highlights: 2 concrete engineering feats implemented.
4. Red Flags / Gaps: 2 missing optimizations or architectural concerns.
5. 3 Direct Oral Questions to ask the student right now in the call to verify they wrote the code themselves.

Keep it crisp, actionable, and under 200 words.
"""

MODELS_TO_TRY = [
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3.5-flash",
    "gemini-2.5-flash"
]

@app.get("/", response_class=HTMLResponse)
def upload_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Student Project Report Portal</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
            .card { background: #1e293b; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); width: 100%; max-width: 440px; text-align: center; }
            h2 { margin-bottom: 0.5rem; color: #38bdf8; }
            p { color: #94a3b8; font-size: 0.95rem; margin-bottom: 1.5rem; }
            input[type="file"] { display: none; }
            .drop-zone { border: 2px dashed #475569; border-radius: 8px; padding: 2rem 1rem; cursor: pointer; display: block; margin-bottom: 1rem; }
            .drop-zone:hover { border-color: #38bdf8; background: #334155; }
            button { background: #38bdf8; color: #0f172a; border: none; padding: 0.8rem 1.5rem; border-radius: 8px; font-weight: 600; cursor: pointer; width: 100%; }
            button:hover { background: #0ea5e9; }
            #status { margin-top: 1rem; font-size: 0.9rem; color: #34d399; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Intern Review Portal</h2>
            <p>Upload your Project PDF Report here for Priya to audit during the call.</p>
            <form id="uploadForm">
                <label class="drop-zone" for="fileInput" id="dropLabel">
                    <span>Click or Drag & Drop Project PDF</span>
                    <input type="file" id="fileInput" accept=".pdf" required>
                </label>
                <button type="submit" id="btn">Submit to Priya</button>
            </form>
            <div id="status"></div>
        </div>

        <script>
            const form = document.getElementById('uploadForm');
            const fileInput = document.getElementById('fileInput');
            const dropLabel = document.getElementById('dropLabel');
            const statusDiv = document.getElementById('status');
            const btn = document.getElementById('btn');

            fileInput.onchange = () => {
                if (fileInput.files[0]) dropLabel.innerText = fileInput.files[0].name;
            };

            form.onsubmit = async (e) => {
                e.preventDefault();
                if (!fileInput.files[0]) return;
                
                btn.disabled = true;
                btn.innerText = "Analyzing Report with Gemini...";
                statusDiv.innerText = "Uploading & extracting project specs...";

                const formData = new FormData();
                formData.append("file", fileInput.files[0]);

                try {
                    const res = await fetch("/api/upload-report", { method: "POST", body: formData });
                    const text = await res.text();
                    
                    let data;
                    try {
                        data = JSON.parse(text);
                    } catch (parseErr) {
                        statusDiv.style.color = "#ef4444";
                        statusDiv.innerText = "Server Error: " + text.slice(0, 100);
                        btn.disabled = false;
                        btn.innerText = "Try Again";
                        return;
                    }

                    if (data.status === "success") {
                        statusDiv.style.color = "#34d399";
                        statusDiv.innerText = "✓ Report verified! Priya has loaded your project.";
                        btn.innerText = "Uploaded Successfully";
                    } else {
                        statusDiv.style.color = "#ef4444";
                        statusDiv.innerText = "Upload failed: " + data.message;
                        btn.disabled = false;
                        btn.innerText = "Try Again";
                    }
                } catch (err) {
                    statusDiv.style.color = "#ef4444";
                    statusDiv.innerText = "Network error: " + err;
                    btn.disabled = false;
                    btn.innerText = "Try Again";
                }
            };
        </script>
    </body>
    </html>
    """

@app.post("/api/upload-report")
async def upload_report(file: UploadFile = File(...)):
    dest_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save the file to disk
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"\n[+] Saved file locally: {dest_path}")
    print("[+] Uploading file to Gemini File API...")

    try:
        uploaded_file = client.files.upload(file=dest_path)
    except Exception as e:
        print(f"[!] File upload to Gemini failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Gemini File API error: {str(e)}"})

    briefing_text = None
    for model_name in MODELS_TO_TRY:
        try:
            print(f"[+] Analyzing report with {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=[uploaded_file, "Generate the technical audit briefing for Priya."],
                config=types.GenerateContentConfig(
                    system_instruction=REPORT_ANALYSIS_PROMPT,
                    temperature=0.2
                )
            )
            briefing_text = response.text.strip()
            print(f"[✓] Analysis generated via {model_name}")
            break
        except Exception as e:
            print(f"[!] Model {model_name} failed: {str(e)[:80]}")
            continue

    if not briefing_text:
        return JSONResponse(status_code=500, content={"status": "error", "message": "All Gemini models failed to analyze the PDF."})

    # Save briefing to current_briefing.json for meet_live_audio.py
    with open(BRIEFING_FILE, "w", encoding="utf-8") as f:
        json.dump({"briefing": briefing_text, "filename": file.filename}, f, indent=2)

    return {"status": "success", "message": "Audited", "briefing": briefing_text}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)