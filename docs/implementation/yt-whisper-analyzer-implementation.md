# YouTube Whisper Analyzer Implementation

## Project Structure
```
yt-whisper-analyzer/
├── docs/                      # Documentation
│   ├── design/                # Design decisions and plans
│   ├── implementation/        # Implementation details
│   └── reflections/           # Learnings and reflections
│   └── usage_guide.md         # Usage instructions
├── src/                       # Source code
│   ├── __init__.py            # Package initialization
│   ├── downloader.py          # YouTube video downloading with yt-dlp
│   ├── transcriber.py         # Whisper API integration with chunking
│   ├── analyzer.py            # Transcript analysis
│   ├── formatter.py           # Output formatting
│   └── main.py                # CLI and main function
├── output/                    # Directory for output files
├── ffmpeg.exe                 # FFmpeg executable for audio processing
├── ffprobe.exe                # FFprobe executable for media analysis
├── .env.template              # Template for environment configuration
├── .gitignore                 # Git ignore file
├── requirements.txt           # Project dependencies
├── README.md                  # Project overview
├── .cursorrules               # Project tracking and planning
└── run_analysis.py            # Quick start script
```

## Implementation Details

### downloader.py
This module handles the downloading of YouTube videos using yt-dlp for improved reliability.

```python
import os
import re
import subprocess
import shutil
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    # Handle different URL formats
    # Return video ID

def find_ffmpeg():
    """Find ffmpeg executable in the system or project directory"""
    # Check in PATH
    # Check in project root
    # Return path to ffmpeg or None

def download_with_yt_dlp(url, output_filename):
    """Download audio from YouTube using yt-dlp"""
    # Find ffmpeg
    # Configure yt-dlp options
    # Download audio
    # Return path to downloaded file

def download_audio(video_id_or_url, output_filename="downloaded_audio"):
    """Download audio from YouTube video"""
    # Determine if input is URL or ID
    # Download audio using yt-dlp
    # Return path to downloaded file
```

### transcriber.py
This module handles the integration with the Groq API for Whisper transcription, including support for large files by splitting them into chunks.

```python
import os
import json
import tempfile
import subprocess
import shutil
from pathlib import Path
from groq import Groq
from pydub import AudioSegment
from dotenv import load_dotenv

def load_api_key():
    """Load Groq API key from .env file or environment variables"""
    # Try to load from .env file
    # Fall back to environment variable
    # Return API key or None

def get_file_size(file_path):
    """Get the size of a file in bytes"""
    # Return file size

def find_ffmpeg_tools():
    """Find ffmpeg and ffprobe executables"""
    # Check in environment variables
    # Check in PATH
    # Check in project root and common locations
    # Return paths to ffmpeg and ffprobe

def split_audio_file_with_ffmpeg(audio_file, max_size, chunk_duration):
    """Split an audio file into smaller chunks using ffmpeg directly"""
    # Check if file needs splitting
    # Find ffmpeg and ffprobe
    # Get audio duration using ffprobe
    # Calculate number of chunks based on duration
    # Create chunks using ffmpeg with appropriate settings
    # Return list of chunk files

def split_audio_file(audio_file, max_size, chunk_duration):
    """Split an audio file into smaller chunks"""
    # Try ffmpeg direct method first
    # Fall back to pydub if needed
    # Return list of chunk files

def transcribe_audio_chunk(audio_file, client, model):
    """Transcribe a single audio chunk"""
    # Check file size
    # Send to Groq API
    # Handle different response types
    # Return transcript text

def transcribe_audio(audio_file, api_key=None, model="whisper-large-v3"):
    """Transcribe audio using Whisper API via Groq"""
    # Load API key if not provided
    # Initialize Groq client
    # Check if file needs splitting based on size
    # Split audio into chunks if needed
    # Try quality reduction if splitting fails
    # Transcribe each chunk with proper error handling
    # Combine transcripts from successful chunks
    # Clean up temporary files
    # Return full transcript

def save_transcript(transcript, output_file):
    """Save transcript to a file"""
    # Write transcript to file
    # Return success status
```

### analyzer.py
This module analyzes transcripts for keyword occurrences.

```python
import re
import json

def count_keywords(transcript, keywords):
    """Count occurrences of keywords in transcript"""
    # Convert transcript to lowercase for case-insensitive matching
    # Count occurrences of each keyword
    # Return statistics
```

### formatter.py
This module formats the analysis results for output.

```python
import json

def format_results(analysis_results, format_type="text"):
    """Format analysis results for output"""
    # Format results according to specified format
    # Return formatted output
```

### main.py
This module serves as the entry point and CLI interface.

```python
import argparse
import os
from .downloader import download_audio
from .transcriber import transcribe_audio
from .analyzer import count_keywords
from .formatter import format_results

def main():
    """Main entry point for the application"""
    # Parse command line arguments
    # Execute pipeline:
    #   1. Download video
    #   2. Transcribe audio
    #   3. Analyze transcript
    #   4. Format and output results
```

## Integration Points

### YouTube to Whisper
The output from the downloader module (audio file) is the input to the transcriber module.

### Whisper to Analyzer
The output from the transcriber module (transcript) is the input to the analyzer module.

### Analyzer to Formatter
The output from the analyzer module (analysis results) is the input to the formatter module.

## Error Handling

Each module implements comprehensive error handling:

1. **Downloader**: 
   - Handles network issues, invalid URLs, unavailable videos
   - Implements retry mechanism with progressive backoff
   - Falls back to alternative download methods if primary method fails
   - Properly detects and configures ffmpeg

2. **Transcriber**: 
   - Handles API errors, rate limits, malformed responses
   - Splits large files into manageable chunks
   - Handles different API response formats
   - Properly manages temporary files
   - Implements robust ffmpeg and ffprobe detection
   - Provides detailed logging of chunking process
   - Handles failures in individual chunks gracefully

3. **Analyzer**: 
   - Handles text processing errors, empty transcripts
   - Provides robust keyword matching

4. **Formatter**: 
   - Handles output formatting issues
   - Supports multiple output formats

## Environment Configuration

The project uses a `.env` file for configuration:

```
# Groq API Key
GROQ_API_KEY=your_api_key_here

# Default Whisper Model
WHISPER_MODEL=whisper-large-v3
```

This approach keeps sensitive information like API keys out of the code and command history.

## Handling Large Files

For large audio files that exceed the Groq API's size limit (25MB):

1. The file is split into smaller chunks using ffmpeg:
   - Audio duration is detected using ffprobe
   - Chunks are created based on duration rather than file size
   - Each chunk is encoded with optimized settings (mono, reduced bitrate)
   - Proper error handling ensures the process continues even if some chunks fail

2. Each chunk is transcribed separately:
   - Chunks are processed sequentially
   - Detailed logging tracks progress
   - Errors in individual chunks don't stop the entire process

3. The transcripts are combined into a single result:
   - Successful chunks are joined with proper spacing
   - Warning is provided if some chunks failed

4. Temporary files are cleaned up automatically:
   - Temporary directories are removed after processing
   - Original audio file is preserved

5. If chunking fails, quality reduction is attempted:
   - Audio is converted to mono with lower bitrate
   - Sample rate is reduced
   - If still too large, chunking is attempted again

## FFmpeg Integration

The tool requires ffmpeg and ffprobe for handling large audio files:

1. **Automatic Detection**:
   - Checks environment variables (FFMPEG_PATH, FFPROBE_PATH)
   - Searches in PATH
   - Looks in common installation locations
   - Checks project root directory

2. **Required Files**:
   - ffmpeg.exe: For audio processing and conversion
   - ffprobe.exe: For media analysis and duration detection

3. **Installation**:
   - Windows users should place ffmpeg.exe and ffprobe.exe in the project root
   - macOS/Linux users can install via package managers

4. **Error Handling**:
   - Clear warnings if ffmpeg/ffprobe not found
   - Fallback to alternative methods if possible
   - Detailed error messages to help troubleshoot

## YouTube Download Reliability

To improve reliability of YouTube downloads:

1. Replaced pytube with yt-dlp, which is more robust against YouTube's restrictions
2. Added proper ffmpeg detection and configuration
3. Implemented retry mechanism with progressive backoff
4. Added fallback methods if primary download method fails

## Testing Approach

1. Unit tests for each module function
2. Integration tests for the complete pipeline
3. Testing with a variety of YouTube videos (short/long, different content types)
4. Testing with different keywords and patterns
5. Verification of chunking process with large files
6. Validation of transcript completeness and accuracy 