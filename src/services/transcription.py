"""Transcription Service using Faster Whisper"""
from pathlib import Path
from typing import List
from faster_whisper import WhisperModel

from src.models.video import TranscriptionSegment

class TranscriptionService:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize Whisper model.
        Args:
            model_size: Size of the model (tiny, base, small, medium, large-v2)
            device: Device to use (cpu, cuda, auto)
            compute_type: Quantization type (int8, float16, float32)
        """
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: Path) -> List[TranscriptionSegment]:
        """
        Transcribe audio file.
        Returns a list of TranscriptionSegment Pydantic models.
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Check if file has audio stream
        import av
        try:
            with av.open(str(audio_path)) as container:
                if not container.streams.audio:
                    print(f"Warning: No audio stream found in {audio_path}")
                    return []
        except Exception as e:
            print(f"Warning: Failed to check audio stream: {e}")
            # Continue and let whisper try, or return empty?
            # Safer to return empty if we can't verify
            return []

        segments, info = self.model.transcribe(str(audio_path), beam_size=5)
        
        result = []
        for segment in segments:
            result.append(TranscriptionSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text.strip()
            ))
            
        return result
