# Cut.py: An AI-Powered Video Highlight Generator

Welcome to **Cut.py**, my personal project where I'm building an intelligent video processing pipeline. I designed this tool to automatically generate engaging highlights from long-form videos using the power of local AI models.

## 🚀 What I've Built So Far

I've created a robust, privacy-focused video editor that runs entirely on your local machine. No data leaves your server. Here's what makes it special:

- **🤖 Local AI Analysis**: I integrated **Llama 3** (via `llama.cpp`) to "watch" the video transcripts and understand context. It doesn't just cut randomly; it finds the _best_ parts.
- **🗣️ User-Directed Cuts**: I added a feature where you can tell the AI exactly what to look for. Want the "funniest moment" or "the part about the budget"? Just ask.
- **🐳 Dockerized FFmpeg**: I solved the "it works on my machine" problem for video processing. All video cutting happens inside a **Docker container**, ensuring consistent results regardless of your host OS (and fixing those annoying Apple Silicon warnings).
- **📝 Precision Transcription**: Using **Faster Whisper** to generate highly accurate subtitles and transcripts, which serve as the foundation for the AI's understanding.
- **🎬 Smart Scene Detection**: Using `PySceneDetect` to ensure cuts happen at natural scene boundaries, avoiding jarring transitions.

## 🛠️ How It Works (Under the Hood)

When you upload a video to my API, here's the journey it takes:

1.  **Ingestion**: The video is saved, and I generate a unique ID.
2.  **Scene Detection**: Scan the video for visual cuts to understand the visual structure.
3.  **Transcription**: Extract the audio and transcribe it using the Whisper model.
4.  **AI Analysis**: This is the cool part. I feed the transcript and scene data into a local LLM (Mistral/Llama).
    - _Default Mode_: It looks for the most engaging segment.
    - _Prompt Mode_: If you provided a prompt (e.g., "Find the demo"), it searches for that specific content.
5.  **Intelligent Cutting**: Once the best segment is identified, I calculate the exact timestamps.
6.  **Processing**: Spin up a Docker container to run FFmpeg and surgically extract the clip without re-encoding (stream copy) for blazing fast speed.

## 📦 Installation & Setup

I'm sharing here how you can set up my project on your own machine.

### Prerequisites

- **Python 3.13+**
- **Docker** (for the video processing container)
- **uv** (my preferred package manager)

### Step 1: Clone and Install

```bash
git clone <repo-url>
cd cut_py
uv sync
```

### Step 2: Set up Models

I wrote a script to download the necessary GGUF models for the LLM.

```bash
./setup_models.sh
```

### Step 3: Build the Docker Image

You need the FFmpeg container image for the video editing service to work.

```bash
docker build -t ffmpeg-container -f docker/ffmpeg-multiarch.Dockerfile .
```

### Step 4: Run the Server

```bash
./start.sh
```

The API will be available at `http://localhost:8000`.

## 🎮 Usage Guide

I've made the API very simple to use. Here is an example of how to generate a highlight.

### Auto-Highlight

Let the AI decide what's best.

```bash
curl -X POST "http://localhost:8000/highlight/process" \
  -F "video=@/path/to/my_video.mp4" \
  -F "target_duration=30" \
  --output highlight.mp4
```

### Directed Highlight (New Feature!)

Tell the AI what you want.

```bash
curl -X POST "http://localhost:8000/highlight/process" \
  -F "video=@/path/to/podcast.mp4" \
  -F "target_duration=60" \
  -F "prompt=Find the segment where they discuss the release date" \
  -F "prompt=Find the segment where they discuss the release date" \
  --output release_date_clip.mp4
```

### YouTube Processing (New Feature!)

Process a video directly from YouTube.

```bash
curl -X POST "http://localhost:8000/highlight/process-url" \
  -F "youtube_url=https://www.youtube.com/watch?v=YOUR_VIDEO_ID" \
  -F "target_duration=30" \
  --output highlight.mp4
```

## 🏗️ Tech Stack

- **Framework**: FastAPI
- **AI/LLM**: Llama.cpp (Python bindings), Faster Whisper
- **Video Processing**: FFmpeg (Dockerized), PySceneDetect
- **Package Manager**: uv

---

