"""Highlight Generation API"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
from fastapi.responses import FileResponse

from src.services.video import VideoService
from src.services.highlight import HighlightService

router = APIRouter(tags=["highlight"])

@router.post("/highlight/process", response_class=FileResponse)
async def process_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    target_duration: float = Form(30.0),
    prompt: Optional[str] = Form(None)
):
    """
    Process video upload to generate a highlight.
    """
    video_path = await VideoService.save_upload(video)
    return await HighlightService.process_video_pipeline(
        video_path, target_duration, prompt, background_tasks
    )

@router.post("/highlight/process-url", response_class=FileResponse)
async def process_video_url(
    background_tasks: BackgroundTasks,
    youtube_url: str = Form(...),
    target_duration: float = Form(30.0),
    prompt: Optional[str] = Form(None)
):
    """
    Process YouTube video to generate a highlight.
    """
    # Download the video first
    try:
        video_path = VideoService.download_from_url(youtube_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return await HighlightService.process_video_pipeline(
        video_path, target_duration, prompt, background_tasks
    )
