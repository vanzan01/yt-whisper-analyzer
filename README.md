# 🎬 YouTube Whisper Analyzer

> *Accurately detect sponsor mentions and keywords in YouTube videos using AI transcription*

This tool helps you find and count how often specific brands, sponsors, or keywords appear in YouTube videos without having to watch the entire video. Unlike tools that rely on YouTube's built-in captions (which are often inaccurate), this analyzer uses Whisper AI to create high-quality transcripts, ensuring you catch all keyword mentions.

## ✨ What This Tool Does

- 📥 Downloads audio from any YouTube video
- 🎙️ Creates highly accurate transcripts using Whisper AI (much better than YouTube's automatic captions)
- 🔍 Finds all mentions of sponsors or keywords in the transcript with precision
- 📊 Shows you exactly when and where sponsor mentions appear with timestamps
- 💾 Saves results to view later
- 🔄 Works even on videos without captions or with poor automatic captions

### Why Whisper AI Transcription Matters

YouTube's automatic captions often miss words, mispronounce names, and struggle with technical terms or accents. This means you might miss important sponsor mentions when using YouTube's transcripts.

By using state-of-the-art Whisper AI (through the Groq API), this tool delivers:
- Higher accuracy for brand names and technical terms
- Better handling of different accents and speech patterns
- More reliable timestamp information
- Detection of mentions that YouTube's captions would miss completely

This accuracy is crucial when you need to find every instance of a keyword or analyze how frequently a sponsor is mentioned.

## 🛠️ Quick Start for Beginners

1. **Install Python** (if you don't already have it)
   - Download from [python.org](https://www.python.org/downloads/) (version 3.9 or newer)
   - During installation, check "Add Python to PATH"

2. **Download this tool**
   - Download and unzip this repository to a folder on your computer

3. **Install required packages**
   - Open Command Prompt (Windows) or Terminal (Mac)
   - Navigate to the folder where you unzipped the files
   - Run this command:
     ```
     pip install -r requirements.txt
     ```

4. **Set up your API key** (needed for transcription)
   - Create a file named `.env` in the main folder
   - Add this line to the file, replacing YOUR_KEY with your Groq API key:
     ```
     GROQ_API_KEY=YOUR_KEY
     ```
   - Save the file

5. **Install FFmpeg** (for audio processing)
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Extract the files and place ffmpeg.exe and ffprobe.exe in the same folder as this tool

## 📋 How to Use

### ✅ Option 1: Interactive Mode (Easiest)

Simply run:
```
python run_analysis.py --interactive
```

This will guide you through each step with simple questions:
1. Enter a YouTube URL or video ID
2. Enter keywords to search for (separated by commas)
3. Choose transcript options
4. Select save options (results are saved by default)
5. Follow the prompts for remaining options

### ✅ Option 2: Command Line Mode

If you prefer typing a single command:
```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "Bybit, exchange" --save_results
```

Replace:
- `VIDEO_ID` with the YouTube video ID (or use the full URL)
- `"Bybit, exchange"` with your sponsor names or keywords

### 📊 Viewing Saved Results Later

When you run an analysis, two files are automatically saved:
1. The formatted output you see on screen
2. A raw data file that can be viewed again later

To view your saved results:

#### ✅ Option 1: Interactive Viewer (Recommended)

Run:
```
python view_analysis.py --interactive
```

This will:
1. Show you a list of all your saved analyses
2. Display each file with:
   - The video ID
   - Date of analysis
   - File size
   - Keywords that were analyzed
3. Use arrow keys to select the file you want to view
4. Press Enter to view the full results

You'll see a selection menu like:
```
? Select an analysis file to view:
 » WFndPuge5yE (2025-03-15 10:37:06) - 0.31MB - Keywords: Bybit, exchange
   dQw4w9WgXcQ (2023-04-15 12:34:56) - 0.25MB - Keywords: Binance, crypto, Bitcoin
   [Specify a different file path]
```

#### ✅ Option 2: Direct File Path

If you know which file you want to view:
```
python view_analysis.py output/analysis_VIDEO_ID_TIMESTAMP_raw.json
```

## 📝 Examples

### Example 1: Detect sponsor mentions interactively

```
python run_analysis.py --interactive
```

Then follow the prompts:
- Enter URL: `https://www.youtube.com/watch?v=WFndPuge5yE`
- Enter keywords: `Bybit, exchange`
- Select options as prompted

### Example 2: Detect sponsor mentions with one command

```
python run_analysis.py --url https://www.youtube.com/watch?v=WFndPuge5yE --keywords "Bybit, exchange" --save_results
```

### Example 3: View saved results

```
python view_analysis.py --interactive
```

Then select the analysis you want to view from the list.

### Example 4: Analyze a crypto podcast for mentions

```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "Bitcoin,Solana" --output json
```

### Example 5: Track multiple sponsors in a video

```
python run_analysis.py --url https://www.youtube.com/watch?v=VIDEO_ID --keywords "Bybit,NordVPN" --save_transcript
```

## ❓ Common Issues & Solutions

**"Missing API key" error**
- Make sure you created the `.env` file with your API key
- Check that the file is in the main folder and has no other file extension

**"FFmpeg not found" error**
- Make sure ffmpeg.exe and ffprobe.exe are in the same folder as the tool
- If you're on Mac/Linux, install FFmpeg using your package manager

**"No results found" for keywords**
- Try different variations of your keywords (singular/plural forms)
- Check for typos in your keywords
- Try using simpler keywords

**"'python' is not recognized" error**
- Make sure Python is installed and added to your PATH
- Try using `py` instead of `python` on Windows
- Open a new Command Prompt window after installing Python

**YouTube Download Issues**
- The tool uses yt-dlp which is more robust against YouTube's restrictions
- Some videos may have restrictions that prevent downloading
- If you see "403 Forbidden" errors, the tool will automatically retry with different methods

**Audio Processing Issues**
- For "Error splitting audio file" errors, try manually reducing the audio quality before processing

**Need more help?**
- Run the tool with `--help` for a list of all available options:
  ```
  python run_analysis.py --help
  ```

## 📚 Technical Details

### Prerequisites

1. Python 3.6 or higher
2. A Groq API key (for Whisper API access)
3. Internet connection
4. ffmpeg and ffprobe (required for handling large files)

### Installation (For Developers)

1. Clone this repository:
```
git clone https://github.com/vanzan01/yt-whisper-analyzer.git
cd yt-whisper-analyzer
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Set up your Groq API key using one of these methods:

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
   
   Pass your API key directly using the `--api_key` parameter.

### Command Line Options (Full List)

#### Analysis Options

- `--url URL`: YouTube video URL
- `--video_id VIDEO_ID`: YouTube video ID (alternative to URL)
- `--keywords "word1, word2"`: Comma-separated list of keywords to analyze
- `--output`: Output format (text, json) [default: text]
- `--model`: Whisper model to use [default: from .env or "whisper-large-v3"]
- `--api_key`: Groq API key (alternatively, set in .env file or as environment variable)
- `--save_transcript`: Save transcript to file
- `--save_results`: Save analysis results to file
- `--output_dir`: Directory for output files [default: "output"]
- `--transcript_file`: Path to a local transcript file to use instead of downloading and transcribing
- `--use_existing_transcript`: Look for an existing transcript in the output directory before downloading and transcribing
- `--interactive`, `-i`: Run in interactive mode with guided setup and visual UI
- `--no-banner`: Hide the CryptoBanter ASCII art banner

#### Viewing Options

- `--interactive`: Select from saved files
- `file`: Direct path to a specific file

### Configuration via .env

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
- `whisper-large-v3`: Best accuracy, multilingual support, most detailed
- `whisper-large-v3-turbo`: Good balance of speed and accuracy
- `distil-whisper-large-v3-en`: Fastest option, English-only

### How It Works

#### YouTube Download Process
The tool uses yt-dlp to reliably download audio from YouTube videos, even when facing restrictions that would block other libraries.

#### Handling Large Audio Files
For large audio files that exceed the Groq API's 25MB size limit:

1. The file is automatically split into smaller chunks using ffmpeg
2. Each chunk is transcribed separately
3. The transcripts are combined into a single result
4. If chunking fails, quality reduction is attempted

This process happens automatically and is transparent to the user.

#### Visual Progress Indicators
When transcribing large files, the tool shows:
- Visual progress bars for audio chunking
- Transcription progress indicators with estimated time remaining
- Colorful status messages for better visibility
- Clearly marked timestamps in results

### Requirements

- Python 3.6+
- groq
- python-dotenv
- yt-dlp
- pydub
- ffmpeg and ffprobe
- Internet connection

### Acknowledgements

This project builds upon existing work from the banter-get-transcripts repository. 

## 📜 License

This project is licensed under the MIT License - see below for details.

### MIT License

Copyright (c) 2023 YouTube Whisper Analyzer Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

### What This License Means

The MIT License is a permissive license that allows you to:

- ✅ Use this software for commercial purposes
- ✅ Modify the software as needed
- ✅ Distribute modified versions
- ✅ Use it privately or publicly
- ✅ Include it in your own projects (open source or commercial)

The only requirement is that you must include the same MIT License and copyright notice in any copies or substantial portions of the software that you distribute. You do not need to mention or credit this project in your documentation, presentations, videos, or other non-code contexts.

### Attribution Request

While the MIT license doesn't legally require it, we kindly ask that you consider giving credit to the YouTube Whisper Analyzer project when you use it in your work. A simple acknowledgment like "Powered by YouTube Whisper Analyzer" or a link to this repository in your documentation, description, or credits would be greatly appreciated. This helps increase awareness of the tool and contributes to building a community of users.

Example credit line:
```
This analysis was performed using YouTube Whisper Analyzer (https://github.com/vanzan01/yt-whisper-analyzer)
```

Thank you for your support!