# YouTube Whisper Analyzer Usage Guide

This guide will walk you through setting up and using the YouTube Whisper Analyzer tool to analyze keyword frequency in YouTube videos.

## Prerequisites

1. Python 3.6 or higher
2. A Groq API key (for Whisper API access)
3. Internet connection
4. ffmpeg and ffprobe (required for handling large files)

## Installation

1. Clone or download the repository:
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
     - Extract the archive and copy `ffmpeg.exe` and `ffprobe.exe` to the project root directory (yt-whisper-analyzer/)
     - Alternatively, add ffmpeg to your PATH environment variable
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `apt-get install ffmpeg` or equivalent for your distribution

4. Set up your Groq API key:

   ### Option 1: Using .env file (Recommended)
   
   Copy the template file:
   ```
   cp .env.template .env
   ```
   
   Edit the `.env` file and replace `your_api_key_here` with your actual Groq API key:
   ```
   # YouTube Whisper Analyzer Environment Configuration
   
   # Groq API Key - Replace with your actual API key
   GROQ_API_KEY=your_actual_api_key_here
   
   # Optional: Default Whisper Model
   WHISPER_MODEL=whisper-large-v3
   ```
   
   ### Option 2: Environment Variables
   ```
   # On Windows (Command Prompt)
   set GROQ_API_KEY=your_api_key_here
   
   # On Windows (PowerShell)
   $env:GROQ_API_KEY="your_api_key_here"
   
   # On macOS/Linux
   export GROQ_API_KEY=your_api_key_here
   ```
   
   ### Option 3: Command Line Parameter
   Provide the API key directly when running the tool (see examples below).

## Basic Usage

The simplest way to use the tool is by providing a YouTube URL and the keywords you want to analyze:

```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "keyword1,keyword2,keyword3"
```

Or if you have just the video ID:

```
python run_analysis.py --video_id VIDEO_ID --keywords "keyword1,keyword2,keyword3"
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--url` | YouTube video URL |
| `--video_id` | YouTube video ID (alternative to URL) |
| `--keywords` | Comma-separated list of keywords to analyze |
| `--output` | Output format: "text" or "json" (default: "text") |
| `--model` | Whisper model to use (default: from .env or "whisper-large-v3") |
| `--api_key` | Groq API key (alternatively, set in .env file or environment) |
| `--save_transcript` | Save transcript to file |
| `--save_results` | Save analysis results to file |
| `--output_dir` | Directory for output files (default: "output") |
| `--transcript_file` | Path to a local transcript file to use instead of downloading and transcribing |
| `--use_existing_transcript` | Look for an existing transcript in the output directory before downloading and transcribing |
| `--interactive`, `-i` | Run in interactive mode with guided setup and visual UI |
| `--no-banner` | Hide the CryptoBanter ASCII art banner |

## Interactive Mode

The tool now features an interactive mode that guides you through setting up your analysis. To use it:

```
python run_analysis.py --interactive
```

Or use the dedicated interactive script:

```
python interactive_analyzer.py
```

### Features of Interactive Mode

- **Guided Setup**: Step-by-step prompts to configure your analysis
- **User-friendly Selection**: Easy navigation through options with arrow keys
- **Visual Feedback**: Colorful UI with clear indications of what's happening
- **Smart Defaults**: Pre-filled default values for common options
- **Input Validation**: Immediate feedback on invalid inputs

### Interactive Workflow

When using interactive mode, you'll be guided through the following steps:

1. **Video Source**: Choose between YouTube URL or Video ID
2. **Keywords**: Enter the keywords you want to analyze (comma-separated)
3. **Transcript Options**: Choose between:
   - Download and transcribe new
   - Check for existing transcript first
   - Specify a local transcript file
4. **Save Options**: Select which outputs to save:
   - Save transcript
   - Save analysis results
5. **Output Format**: Choose between text or JSON
6. **Output Directory**: Specify where to save files
7. **API Key**: Enter your Groq API key if not set in environment
8. **Model Selection**: Choose the Whisper model to use

This workflow makes it much easier for new users to understand all available options and ensures all necessary information is provided before starting the analysis.

## Visual Progress Indicators

The tool now provides visual feedback during processing:

### Download Progress
- Shows download progress from YouTube
- Indicates when download is complete

### Transcription Progress
- Progress bars for audio chunking
- Per-chunk transcription status
- Estimated time remaining
- Total progress across all chunks

### Analysis Progress
- Visual indication of analysis steps
- Spinner during keyword processing

All these visual elements help you understand what's happening during longer operations and provide an estimate of how long processing will take.

## CryptoBanter ASCII Art

The tool includes a colorful ASCII art banner for CryptoBanter. To hide this banner:

```
python run_analysis.py --no-banner [other options]
```

## Configuration via .env File

The .env file allows you to configure default settings without hard-coding them in scripts or passing them on the command line.

### Available Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `GROQ_API_KEY` | Your Groq API key | None (required) |
| `WHISPER_MODEL` | Default Whisper model to use | whisper-large-v3 |
| `FFMPEG_PATH` | Custom path to ffmpeg executable | Auto-detected |
| `FFPROBE_PATH` | Custom path to ffprobe executable | Auto-detected |

### Whisper Model Options

| Model | Description | Best For |
|-------|-------------|----------|
| `whisper-large-v3` | High accuracy, multilingual support | Most accurate transcription when quality matters most |
| `whisper-large-v3-turbo` | Good balance of speed and accuracy | Faster processing with good quality |
| `distil-whisper-large-v3-en` | Fastest, English-only | English content when speed is a priority |

## Examples

### Analyze brand mentions in a product review

```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "Apple,Samsung,Google" --save_transcript --save_results
```

### Analyze technical terms in a tutorial with a different model

```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "Python,JavaScript,HTML,CSS,React" --output json --model whisper-large-v3-turbo
```

### Analyze specific phrases in a podcast with API key parameter

```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "artificial intelligence,machine learning,neural network" --api_key your_api_key_here
```

### Save transcript to a file for later analysis

```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "keyword1,keyword2" --save_transcript --output_dir "my_transcripts"
```

### Use an existing transcript instead of downloading and transcribing again

```
python run_analysis.py --video_id VIDEO_ID --keywords "keyword1,keyword2" --transcript_file path/to/transcript.txt
```

### Check for existing transcripts before processing

```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "keyword1,keyword2" --use_existing_transcript
```

## Understanding Results

The analysis results include:

1. **Summary Statistics**
   - Total words in transcript
   - Total keyword matches

2. **Keyword Analysis**
   - Exact matches: Words that match exactly with word boundaries
   - Partial matches: Words that contain the keyword as a substring
   - Frequency percentage: How often the keyword appears per 100 words
   - Sample contexts: Short excerpts showing the keyword in context
   - Timestamps: Time markers [HH:MM:SS] indicating when each keyword appears in the video

3. **Related Terms**
   - Words that might be related to your keywords
   - Relationship type (substring, co-occurrence)
   - Number of appearances

## How It Works

### YouTube Download Process

The tool uses yt-dlp, a robust YouTube downloader, to reliably download audio from YouTube videos:

1. The tool extracts the video ID from the provided URL
   - Supports standard YouTube URLs (youtube.com/watch?v=VIDEO_ID)
   - Supports short URLs (youtu.be/VIDEO_ID)
   - Supports live URLs (youtube.com/live/VIDEO_ID)
   - Accepts direct video IDs
2. It downloads the audio using yt-dlp with optimized settings
3. The audio is saved as an MP3 file for transcription

### Handling Large Audio Files

For large audio files that exceed the Groq API's size limit (25MB):

1. The file is automatically split into smaller chunks using ffmpeg:
   - Audio duration is detected using ffprobe
   - Chunks are created based on duration rather than file size
   - Each chunk is encoded with optimized settings (mono, reduced bitrate)

2. Each chunk is transcribed separately:
   - Chunks are processed sequentially
   - Detailed logging tracks progress
   - Errors in individual chunks don't stop the entire process

3. The transcripts are combined into a single result:
   - Successful chunks are joined with proper spacing
   - Warning is provided if some chunks failed

4. If chunking fails, quality reduction is attempted:
   - Audio is converted to mono with lower bitrate
   - Sample rate is reduced
   - If still too large, chunking is attempted again

This process is transparent to the user and happens automatically when needed.

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure your Groq API key is correctly set in the .env file or environment
   - Check if your API key has the necessary permissions/quota
   - If using a .env file, make sure it's in the correct location (project root)

2. **Network Issues**
   - Check your internet connection
   - YouTube might be blocking requests if too many are made in quick succession

3. **YouTube Download Issues**
   - If you encounter "403 Forbidden" errors, the tool will automatically retry with different methods
   - Some videos may have restrictions that prevent downloading (e.g., age-restricted content)
   - The tool uses yt-dlp which is more robust against YouTube's restrictions than other libraries

4. **Audio Processing Issues**
   - **Missing ffmpeg/ffprobe**: You'll see errors like "ffmpeg not found" or "ffprobe not found"
     - For Windows: Copy ffmpeg.exe and ffprobe.exe to the project root directory
     - For macOS/Linux: Install via package manager (brew, apt-get, etc.)
   - **Permission issues**: Ensure ffmpeg/ffprobe executables have execution permissions
   - **Path issues**: If ffmpeg is installed but not found, set FFMPEG_PATH and FFPROBE_PATH in .env file
   - **Chunking failures**: If you see "Error splitting audio file", try manually reducing the audio quality before processing

5. **Transcription Issues**
   - Large files are automatically split into smaller chunks for transcription
   - If transcription fails for a specific chunk, the tool will continue with the remaining chunks
   - Check the Groq API status if all transcription attempts fail
   - If you see "All chunks failed to transcribe", verify your API key and network connection
   - Incomplete transcripts may indicate chunking issues - ensure ffmpeg and ffprobe are properly installed

## Advanced Usage

### Processing Multiple Videos

You can create a simple batch script to process multiple videos:

```python
import os
import subprocess

videos = [
    "VIDEO_ID_1",
    "VIDEO_ID_2",
    "VIDEO_ID_3"
]

keywords = "keyword1,keyword2,keyword3"

for video_id in videos:
    subprocess.run([
        "python", "run_analysis.py",
        "--video_id", video_id,
        "--keywords", keywords,
        "--save_transcript",
        "--save_results"
    ])
```

### Customizing the Tool

The modular design makes it easy to customize:

1. Edit `src/analyzer.py` to add more advanced analysis techniques
2. Modify `src/formatter.py` to change the output format
3. Update `src/transcriber.py` to use different transcription models or services
4. Adjust `src/downloader.py` to change YouTube download settings

### Working with Saved Transcripts

If you've saved transcripts using the `--save_transcript` flag, you can analyze them later without re-downloading and transcribing:

1. Locate the saved transcript file in the output directory
2. Use your own text analysis tools or scripts to process the transcript
3. The transcript is saved in plain text format for maximum compatibility 