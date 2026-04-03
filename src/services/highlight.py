import os
import time
import traceback
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from src.services.scene import SceneDetectionService
from src.services.transcription import TranscriptionService
from src.services.analysis import AnalysisService
from src.services.editor import EditingService

DEFAULT_MODEL_PATH = "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
DEFAULT_WHISPER_MODEL = "base"

class HighlightService:
    _analysis_service = None

    @classmethod
    def get_analysis_service(cls):
        if cls._analysis_service is None:
            print(f"Loading Analysis Model from {DEFAULT_MODEL_PATH}...")
            t0 = time.time()
            cls._analysis_service = AnalysisService(model_path=DEFAULT_MODEL_PATH)
            print(f"> Analysis Model loaded in {time.time() - t0:.2f} seconds.")
        return cls._analysis_service

    @classmethod
    async def process_video_pipeline(
        cls,
        video_path: Path,
        target_duration: float,
        prompt: Optional[str],
        background_tasks: BackgroundTasks
    ):
        output_path = None
        
        try:
            print(f"Starting video processing pipeline for: {video_path}")
            pipeline_start = time.time()

            # 2. Detect Scenes
            print("Detecting scenes...")
            t0 = time.time()
            scene_service = SceneDetectionService()
            scenes = scene_service.detect_scenes(video_path)
            print(f"> Scene detection finished in {time.time() - t0:.2f} seconds.")
            
            # 3. Transcribe
            print("Transcribing video...")
            t1 = time.time()
            transcription_service = TranscriptionService(model_size=DEFAULT_WHISPER_MODEL)
            transcript = transcription_service.transcribe(video_path)
            
            if not transcript:
                raise HTTPException(status_code=400, detail="No audio content found in video. Cannot generate highlight based on content.")
            print(f"> Transcription finished in {time.time() - t1:.2f} seconds.")
            
            # 4. Analyze
            print("Analyzing content to choose highlights...")
            t2 = time.time()
            analysis_service = cls.get_analysis_service()
            result = analysis_service.analyze_content(transcript, scenes, target_duration, user_prompt=prompt)
            print(f"> Analysis finished in {time.time() - t2:.2f} seconds.")
            
            # 5. Cut Video
            if not result.highlights:
                raise HTTPException(status_code=400, detail="No suitable highlight found.")
                
            highlight = result.highlights[0]
            output_filename = f"highlight_{video_path.stem}.mp4"
            output_path = video_path.parent / "output" / output_filename
            
            print(f"Cutting video with FFmpeg...")
            t3 = time.time()
            EditingService.cut_video(
                video_path, 
                highlight.start_time, 
                highlight.end_time, 
                output_path
            )
            print(f"> Video cutting finished in {time.time() - t3:.2f} seconds.")
            
            print(f"Pipeline completed successfully in {time.time() - pipeline_start:.2f} seconds.")

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
