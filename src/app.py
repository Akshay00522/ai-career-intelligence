import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, File, Form, HTTPException, UploadFile  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from analyzer.parsers import UnsupportedFormat, read_document  # noqa: E402
from analyzer.service import run_analysis  # noqa: E402

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
METHOD_PATTERN = "^(tfidf|embedding)$"

app = FastAPI(title="AI Career Intelligence & Skill-Gap Analyzer", version="1.0.0")


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(min_length=20)
    jd_text: str = Field(min_length=20)
    method: str = Field(default="tfidf", pattern=METHOD_PATTERN)
    hours_per_week: float = Field(default=10, gt=0, le=80)


def _run(resume_text: str, jd_text: str, method: str, hours: float) -> dict:
    try:
        return run_analysis(resume_text, jd_text, method, hours)
    except ModuleNotFoundError as exc:  # embedding method without sentence-transformers
        raise HTTPException(status_code=501, detail=f"Optional dependency missing: {exc.name}") from exc


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": app.version}


@app.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest) -> dict:
    return _run(req.resume_text, req.jd_text, req.method, req.hours_per_week)


@app.post("/analyze/upload")
async def analyze_upload(
    resume: UploadFile = File(...),
    jd_text: str = Form(..., min_length=20),
    method: str = Form("tfidf", pattern=METHOD_PATTERN),
    hours_per_week: float = Form(10, gt=0, le=80),
) -> dict:
    data = bytearray()

    while chunk := await resume.read(64 * 1024):
        data.extend(chunk)

        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="File too large (limit 5 MB).",
            )

    data = bytes(data)

    try:
        text = read_document(data, resume.filename or "")
    except UnsupportedFormat as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except Exception as exc:  # corrupt PDF/DOCX
        raise HTTPException(status_code=422, detail=f"Could not read the file: {exc}") from exc

    if len(text.strip()) < 20:
        raise HTTPException(status_code=422, detail="No readable text found (scanned PDFs need OCR).")

    return _run(text, jd_text, method, hours_per_week)
