from typing import Dict
import uuid
import asyncio
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..services import service
from ..database import db
from ..tasks import process_audio_task

router = APIRouter(prefix="/transcription", tags=["transcription"])

class ProcessRequest(BaseModel):
    file_path: str
    template_id: str = "universal_summary"

class TaskResponse(BaseModel):
    task_id: str
    status: str

@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """Upload an audio file for processing"""
    try:
        file_path = await service.save_upload(file)
        return {"file_path": file_path, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _run_async_processing(task_id: str, file_path: str, template_id: str):
    asyncio.run(service.process_audio(task_id, file_path, template_id))


@router.post("/process", response_model=TaskResponse)
async def process_audio(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Start a processing task"""
    task_id = str(uuid.uuid4())
    
    # Create task in database
    db.create_task(task_id, request.file_path, request.template_id)
    
    if service.config.use_celery:
        process_audio_task.delay(task_id, request.file_path, request.template_id)
    else:
        background_tasks.add_task(
            _run_async_processing,
            task_id,
            request.file_path,
            request.template_id,
        )
    
    return {"task_id": task_id, "status": "pending"}

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a task"""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/history")
async def get_history(limit: int = 50):
    """Get processing history"""
    return db.get_all_tasks(limit)


@router.get("/tasks/{task_id}/artifacts")
async def get_task_artifacts(task_id: str):
    """Return rendered report and transcript contents"""
    task = db.get_task(task_id)
    if not task or not task.get("result"):
        raise HTTPException(status_code=404, detail="Result not found")
    
    result = task["result"]
    response: Dict[str, str] = {}
    
    report_path = Path(result.get("report_path", ""))
    if report_path.exists():
        response["report_markdown"] = report_path.read_text(encoding="utf-8")
    transcript_path = Path(result.get("transcript_path", ""))
    if transcript_path.exists():
        response["transcript_text"] = transcript_path.read_text(encoding="utf-8")
    pdf_path = Path(result.get("report_pdf_path", ""))
    if pdf_path.exists():
        response["report_pdf_path"] = str(pdf_path)
    
    return response


@router.get("/tasks/{task_id}/download/{kind}")
async def download_artifact(task_id: str, kind: str):
    """Download generated artifacts"""
    task = db.get_task(task_id)
    if not task or not task.get("result"):
        raise HTTPException(status_code=404, detail="Result not found")
    
    result = task["result"]
    mapping = {
        "report-md": result.get("report_path"),
        "report-pdf": result.get("report_pdf_path"),
        "transcript": result.get("transcript_path"),
    }
    
    if kind not in mapping:
        raise HTTPException(status_code=400, detail="Unsupported artifact type")
    
    target = mapping[kind]
    if not target:
        raise HTTPException(status_code=404, detail="Artifact missing")
    
    file_path = Path(target)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")
    
    media_type = "text/plain"
    filename = file_path.name
    if kind == "report-md":
        media_type = "text/markdown"
    elif kind == "report-pdf":
        media_type = "application/pdf"
    elif kind == "transcript":
        media_type = "text/plain"
    
    return FileResponse(file_path, media_type=media_type, filename=filename)
