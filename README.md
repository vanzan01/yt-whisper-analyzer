# YouTube Whisper Analyzer

A command-line tool for downloading YouTube videos, transcribing them using the Whisper API via Groq, analyzing transcripts for keyword frequency, and presenting results in a formatted output.

## Features

- Download audio from YouTube videos using yt-dlp for improved reliability
- Transcribe audio using Whisper API (via Groq)
- Handle large audio files by automatically splitting them into chunks
- Analyze transcripts for keyword occurrences
- Generate formatted reports of keyword frequency
- Simple CLI interface
- Support for .env file to securely store API keys

## Prerequisites

1. Python 3.6 or higher
2. A Groq API key (for Whisper API access)
3. Internet connection
4. ffmpeg and ffprobe (required for handling large files)

## Installation

1. Clone this repository:
```
git clone [repository-url]
cd yt-whisper-analyzer
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. **Important**: Install ffmpeg and ffprobe (required for processing large files):
   - **Windows**: 
     - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
     - Extract the archive and copy `ffmpeg.exe` and `ffprobe.exe` to the project root directory
     - Alternatively, add ffmpeg to your PATH environment variable
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `apt-get install ffmpeg` or equivalent for your distribution

4. Set up your Groq API key:

   **Option 1: Using .env file (recommended)**
   
   Copy the template file and add your API key:
   ```
   cp .env.template .env
   ```
   
   Then edit the `.env` file and replace `your_api_key_here` with your actual Groq API key.
   
   **Option 2: Environment variable**
   ```
   # On Windows (Command Prompt)
   set GROQ_API_KEY=your_api_key_here
   
   # On Windows (PowerShell)
   $env:GROQ_API_KEY="your_api_key_here"
   
   # On macOS/Linux
   export GROQ_API_KEY=your_api_key_here
   ```
   
   **Option 3: Command-line parameter**
   
   Pass your API key directly using the `--api_key` parameter (see Usage below).

## Usage

Basic usage:
```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "keyword1,keyword2,keyword3"
```

Or with video ID:
```
python run_analysis.py --video_id VIDEO_ID --keywords "keyword1,keyword2,keyword3"
```

### Options

- `--url`: YouTube video URL
- `--video_id`: YouTube video ID (alternative to URL)
- `--keywords`: Comma-separated list of keywords to analyze
- `--output`: Output format (text, json) [default: text]
- `--model`: Whisper model to use [default: from .env or "whisper-large-v3"]
- `--api_key`: Groq API key (alternatively, set in .env file or as environment variable)
- `--save_transcript`: Save transcript to file
- `--save_results`: Save analysis results to file
- `--output_dir`: Directory for output files [default: "output"]

## Examples

Count how many times a brand name is mentioned:
```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "Coca-Cola,Pepsi,Sprite"
```

Analyze a podcast for topic frequency:
```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "AI,machine learning,deep learning,neural networks" --output json
```

Save the transcript for later analysis:
```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "keyword1,keyword2" --save_transcript
```

## Configuration via .env

You can configure default settings in the `.env` file:

```
# Groq API Key
GROQ_API_KEY=your_api_key_here

# Default Whisper Model
WHISPER_MODEL=whisper-large-v3

# Optional: Custom paths to ffmpeg and ffprobe
FFMPEG_PATH=/path/to/ffmpeg
FFPROBE_PATH=/path/to/ffprobe
```

Available models:
- `whisper-large-v3`: Best accuracy, multilingual support
- `whisper-large-v3-turbo`: Good balance of speed and accuracy
- `distil-whisper-large-v3-en`: Fastest, English-only

## How It Works

### YouTube Download Process
The tool uses yt-dlp to reliably download audio from YouTube videos, even when facing restrictions that would block other libraries.

### Handling Large Audio Files
For large audio files that exceed the Groq API's 25MB size limit:

1. The file is automatically split into smaller chunks using ffmpeg
2. Each chunk is transcribed separately
3. The transcripts are combined into a single result
4. If chunking fails, quality reduction is attempted

This process happens automatically and is transparent to the user.

## Troubleshooting

### YouTube Download Issues
If you encounter errors when downloading YouTube videos:
1. The tool uses yt-dlp which is more robust against YouTube's restrictions
2. Some videos may have restrictions that prevent downloading (e.g., age-restricted content)
3. If you see "403 Forbidden" errors, the tool will automatically retry with different methods

### Audio Processing Issues
If you encounter issues with audio processing:
1. **Missing ffmpeg/ffprobe**: You'll see errors like "ffmpeg not found" or "ffprobe not found"
   - For Windows: Copy ffmpeg.exe and ffprobe.exe to the project root directory
   - For macOS/Linux: Install via package manager (brew, apt-get, etc.)
2. **Chunking failures**: If you see "Error splitting audio file", try manually reducing the audio quality before processing

### Transcription Issues
If you encounter issues with transcription:
1. If transcription fails for specific chunks, the tool will continue with the remaining chunks
2. If you see "All chunks failed to transcribe", verify your API key and network connection
3. Incomplete transcripts may indicate chunking issues - ensure ffmpeg and ffprobe are properly installed

## Requirements

- Python 3.6+
- groq
- python-dotenv
- yt-dlp
- pydub
- ffmpeg and ffprobe
- Internet connection

## Detailed Documentation

For more detailed information, see the [Usage Guide](docs/usage_guide.md) and [Implementation Details](docs/implementation/yt-whisper-analyzer-implementation.md).

## License

[License information]

## Acknowledgements

This project builds upon existing work from the banter-get-transcripts repository. 