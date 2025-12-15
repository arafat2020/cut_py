"""Highlight Generation API"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
import shutil
import traceback
from pathlib import Path
from typing import Optional

from src.services.video import VideoService
from src.services.scene import SceneDetectionService
from src.services.transcription import TranscriptionService
from src.services.analysis import AnalysisService
from src.services.editor import EditingService
from src.models.analysis import HighlightResponse
from fastapi.responses import FileResponse

router = APIRouter(tags=["highlight"])

DEFAULT_MODEL_PATH = "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
DEFAULT_WHISPER_MODEL = "base"

import os

# Global instance for Singleton pattern
_analysis_service = None

def get_analysis_service():
    global _analysis_service
    if _analysis_service is None:
        print(f"Loading Analysis Model from {DEFAULT_MODEL_PATH}...")
        _analysis_service = AnalysisService(model_path=DEFAULT_MODEL_PATH)
        print("Analysis Model loaded.")
    return _analysis_service

async def process_video_pipeline(
    video_path: Path,
    target_duration: float,
    prompt: Optional[str],
    background_tasks: BackgroundTasks
):
    output_path = None
    
    try:
        # 2. Detect Scenes
        scene_service = SceneDetectionService()
        scenes = scene_service.detect_scenes(video_path)
        
        # 3. Transcribe
        transcription_service = TranscriptionService(model_size=DEFAULT_WHISPER_MODEL)
        transcript = transcription_service.transcribe(video_path)
        
        if not transcript:
            raise HTTPException(status_code=400, detail="No audio content found in video. Cannot generate highlight based on content.")
        
        # 4. Analyze
        # Use singleton instance to avoid reloading model
        analysis_service = get_analysis_service()
        result = analysis_service.analyze_content(transcript, scenes, target_duration, user_prompt=prompt)
        
        # 5. Cut Video
        if not result.highlights:
            raise HTTPException(status_code=400, detail="No suitable highlight found.")
            
        highlight = result.highlights[0]
        output_filename = f"highlight_{video_path.stem}.mp4"
        output_path = video_path.parent / "output" / output_filename
        
        EditingService.cut_video(
            video_path, 
            highlight.start_time, 
            highlight.end_time, 
            output_path
        )
        
        # 6. Prepare Cleanup
        def cleanup_files():
            if video_path and video_path.exists():
                os.remove(video_path)
            if output_path and output_path.exists():
                os.remove(output_path)
                
        background_tasks.add_task(cleanup_files)
        
        # 7. Return Video
        return FileResponse(
            path=output_path, 
            filename=output_filename,
            media_type="video/mp4"
        )

    except Exception as e:
        # Cleanup on error if files exist
        if video_path and video_path.exists():
            try:
                os.remove(video_path)
            except:
                pass
        
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
    return await process_video_pipeline(video_path, target_duration, prompt, background_tasks)

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
        
    return await process_video_pipeline(video_path, target_duration, prompt, background_tasks)
