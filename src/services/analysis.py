"""Analysis Service using Llama.cpp"""
import os
import json
from typing import List, Dict, Any, Tuple
from llama_cpp import Llama
from src.models.analysis import HighlightResponse

class AnalysisService:
    def __init__(self, model_path: str, n_ctx: int = 32768):
        """
        Initialize Llama model.
        Args:
            model_path: Path to the GGUF model file
            n_ctx: Context window size
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Please run ./setup_models.sh to download it.")
            
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=-1,  # Offload all layers to GPU/Metal if available
            verbose=False
        )

    def analyze_content(self, transcript: List[Dict[str, Any]], scenes: List[Tuple[float, float]], target_duration: float, user_prompt: str = None) -> HighlightResponse:
        """
        Analyze transcript and scenes to find the best highlight.
        """
        # Prepare context
        transcript_text = "\n".join([f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}" for s in transcript])
        
        criteria = "Identify the most interesting, funny, or important part of the conversation."
        if user_prompt:
            criteria = f"Find a segment that matches this request: '{user_prompt}'"

        prompt = f"""
You are a professional video editor. Your task is to select the most engaging segment from the video transcript below.
The target duration for the highlight is approximately {target_duration} seconds.

Transcript:
{transcript_text}

Instructions:
1. {criteria}
2. Select a contiguous time range that covers this part.
3. Ensure the duration is close to {target_duration} seconds.
4. Return the result in JSON format matching the schema.

Response:
"""
        
        # Get structured output from LLM
        output = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a video editing assistant that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_object",
                "schema": HighlightResponse.model_json_schema()
            },
            temperature=0.7
        )
        
        content = output["choices"][0]["message"]["content"]
        response = HighlightResponse.model_validate_json(content)

        # Enforce exact target duration
        for highlight in response.highlights:
            center = (highlight.start_time + highlight.end_time) / 2
            half_duration = target_duration / 2
            
            highlight.start_time = max(0.0, center - half_duration)
            highlight.end_time = highlight.start_time + target_duration
            
        return response
