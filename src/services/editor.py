"""Video Editing Service using FFmpeg"""
import subprocess
from pathlib import Path

FFMPEG_CPU_LIMIT = 2.0  # e.g. 2 cores max
FFMPEG_MEMORY_LIMIT = "1g"  # e.g. 1GB RAM max

class EditingService:
    @staticmethod
    def cut_video(input_path: Path, start_time: float, end_time: float, output_path: Path) -> Path:
        """
        Cut video using FFmpeg in Docker.
        Args:
            input_path: Path to input video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Path to save the cut video
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input video not found: {input_path}")
            
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Resolve absolute paths
        input_abs = input_path.resolve()
        output_abs = output_path.resolve()
        
        # Determine mount point (common ancestor)
        # We prefer the 'videos' directory if it's in the path, otherwise common path
        import os
        try:
            common_path = Path(os.path.commonpath([input_abs, output_abs]))
        except ValueError:
            # Paths might be on different drives (Windows) or disjoint
            # Fallback to mounting separate volumes if needed, but for now assume common root
            raise RuntimeError("Input and output files must share a common root directory for Docker mounting")

        # Calculate relative paths for container
        rel_input = input_abs.relative_to(common_path)
        rel_output = output_abs.relative_to(common_path)
        
        # Construct Docker command
        # We mount the common_path to /data
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{common_path}:/data"
        ]
        
        if FFMPEG_CPU_LIMIT is not None:
            cmd.extend(["--cpus", str(FFMPEG_CPU_LIMIT)])
        if FFMPEG_MEMORY_LIMIT is not None:
            cmd.extend(["--memory", str(FFMPEG_MEMORY_LIMIT)])
            
        cmd.extend([
            "ffmpeg-container",
            "-y",  # Overwrite output
            "-ss", str(start_time),
            "-i", f"/data/{rel_input}",
            "-to", str(end_time - start_time),  # Duration (since -ss is before -i)
            "-c", "copy",  # Stream copy
            f"/data/{rel_output}"
        ])
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            raise RuntimeError(f"FFmpeg in Docker failed: {error_msg}")
            
        return output_path
