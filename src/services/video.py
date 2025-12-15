"""Video Service for handling file uploads and storage"""
import shutil
import uuid
from pathlib import Path
from pathlib import Path
from fastapi import UploadFile, HTTPException
import yt_dlp

UPLOAD_DIR = Path("videos")
UPLOAD_DIR.mkdir(exist_ok=True)


class VideoService:
    @staticmethod
    async def save_upload(file: UploadFile) -> Path:
        """Save uploaded file to disk and return path"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        # Generate unique filename to prevent collisions
        file_ext = Path(file.filename).suffix
        if not file_ext:
            file_ext = ".mp4"  # Default to mp4 if no extension
            
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
        
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")
            
        return file_path

    @staticmethod
    def get_path(filename: str) -> Path:
        """Get absolute path for a video file"""
        return UPLOAD_DIR / filename

    @staticmethod
    def download_from_url(url: str) -> Path:
        """Download video from URL using yt-dlp"""
        file_id = str(uuid.uuid4())
        # Template ensuring the file is saved in UPLOAD_DIR with the generated ID
        # but preserving the correct extension
        output_template = str(UPLOAD_DIR / f"{file_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best', # Prefer mp4, fallback to best
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return Path(filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to download video: {str(e)}")
