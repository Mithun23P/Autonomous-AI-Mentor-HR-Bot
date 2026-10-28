import os
import re
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool

from services import analyze_project_submission, generate_mentor_voice, generate_pdf_report
from mailer import send_evaluation_email

app = FastAPI(
    title="AI Intern Mentor & Review Engine",
    version="1.0.0",
    docs_url="/docs"
)

# 1. Setup Storage Directories
BASE_STORAGE = Path("storage")
AUDIO_DIR = BASE_STORAGE / "audio"
REPORTS_DIR = BASE_STORAGE / "reports"
STATIC_DIR = Path("static")

for directory in [AUDIO_DIR, REPORTS_DIR, STATIC_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 2. Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")


def sanitize_filename(name: str) -> str:
    """Removes unsafe characters and replaces whitespace."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip().lower())


# 3. Serve Frontend Home Route
@app.get("/", response_class=HTMLResponse)
async def serve_home():
    html_file = STATIC_DIR / "index.html"
    if not html_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="index.html not found inside static/ folder."
        )
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


# 4. Live Review Upload Endpoint
@app.post("/api/review/upload", status_code=status.HTTP_200_OK)
async def handle_live_review(
    background_tasks: BackgroundTasks,
    student_name: str = Form(...),
    student_email: str = Form(...),
    week_no: int = Form(1),
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith((".pdf", ".txt", ".md")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Upload PDF, Markdown, or Plain Text."
        )

    doc_bytes = await file.read()
    mime_type = file.content_type or "application/pdf"

    # Multimodal AI Analysis with Gemini
    try:
        review_result = await analyze_project_submission(
            student_name=student_name,
            week_number=week_no,
            doc_bytes=doc_bytes,
            mime_type=mime_type
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI Engine failed to parse submission: {str(err)}"
        )

    safe_name = sanitize_filename(student_name)
    audio_filename = f"feedback_{safe_name}_w{week_no}.mp3"
    pdf_filename = f"report_{safe_name}_w{week_no}.pdf"

    audio_path = AUDIO_DIR / audio_filename
    pdf_path = REPORTS_DIR / pdf_filename

    # Generate natural mentor voice
    await generate_mentor_voice(review_result.get("spoken_feedback", ""), str(audio_path))

    # Generate formal PDF report (Threadpool)
    await run_in_threadpool(
        generate_pdf_report,
        review_result,
        student_name,
        week_no,
        str(pdf_path)
    )

    # Background task: Email delivery
    background_tasks.add_task(
        send_evaluation_email,
        to_email=student_email,
        student_name=student_name,
        week_no=week_no,
        pdf_path=str(pdf_path)
    )

    return {
        "status": "success",
        "student_name": student_name,
        "week": week_no,
        "review": review_result,
        "voice_feedback_url": f"/api/review/audio/{audio_filename}",
        "pdf_download_url": f"/api/review/pdf/{pdf_filename}"
    }


# 5. File Retrieval Endpoints
@app.get("/api/review/audio/{filename}")
async def get_audio(filename: str):
    safe_name = Path(filename).name
    file_path = AUDIO_DIR / safe_name
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg")


@app.get("/api/review/pdf/{filename}")
async def get_pdf(filename: str):
    safe_name = Path(filename).name
    file_path = REPORTS_DIR / safe_name
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return FileResponse(file_path, media_type="application/pdf")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)