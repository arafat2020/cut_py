from typing import List, Optional
from pydantic import BaseModel, Field

class Highlight(BaseModel):
    """
    Represents a single video highlight segment.
    """
    start_time: float = Field(..., description="Start time of the highlight in seconds")
    end_time: float = Field(..., description="End time of the highlight in seconds")
    summary: str = Field(..., description="Brief summary of why this segment was selected")
    reason: str = Field(..., description="Detailed reasoning for the selection")

class HighlightResponse(BaseModel):
    """
    Response model for highlight analysis.
    """
    highlights: List[Highlight] = Field(..., description="List of identified highlights options")
