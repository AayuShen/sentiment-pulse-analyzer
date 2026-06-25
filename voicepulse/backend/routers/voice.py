import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form
from celery.result import AsyncResult
from tasks import run as process

rt = APIRouter(prefix="/api/voice", tags=["voice"])
rec_dir = os.path.join(os.path.dirname(__file__), "..", "data", "recordings")

@rt.post("/upload")
async def upload(
    file: UploadFile = File(...),
    cid: str = Form("unknown"),
    lang: str = Form(""),
    call_date: str = Form(""),
    call_time: str = Form("")
):
    os.makedirs(rec_dir, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "wav"
    fname = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(rec_dir, fname)
    with open(path, "wb") as f:
        f.write(await file.read())
    job = process.delay(
        path, cid, lang or None,
        call_date=call_date or None,
        call_time=call_time or None,
        original_name=file.filename
    )
    return {"job_id": job.id, "filename": file.filename}

@rt.get("/status/{job_id}")
async def status(job_id: str):
    res = AsyncResult(job_id)
    meta = {}
    try:
        if isinstance(res.info, dict):
            meta = res.info
    except Exception:
        pass
    result = None
    if res.ready():
        try:
            result = res.result if isinstance(res.result, dict) else {"message": str(res.result)}
        except Exception:
            result = {"message": "unknown"}
    return {
        "job_id": job_id,
        "status": res.status,
        "meta": meta,
        "result": result
    }

@rt.get("/result/{job_id}")
async def result(job_id: str):
    """Fetch full result after job completion (speaker blocks, name, etc)."""
    res = AsyncResult(job_id)
    if res.ready():
        try:
            return res.result if isinstance(res.result, dict) else {"message": str(res.result)}
        except Exception:
            return {"message": "unknown"}
    return {"status": res.status, "message": "Job not yet complete"}

