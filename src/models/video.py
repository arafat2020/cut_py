from pydantic import BaseModel, Field

class SceneSegment(BaseModel):
    """Represents a detected video scene"""
    start_time: float = Field(..., description="Start time of the scene in seconds")
    end_time: float = Field(..., description="End time of the scene in seconds")

class TranscriptionSegment(BaseModel):
    """Represents a transcribed audio segment"""
    start: float = Field(..., description="Start time of the transcription in seconds")
    end: float = Field(..., description="End time of the transcription in seconds")
    text: str = Field(..., description="The spoken text segment")
