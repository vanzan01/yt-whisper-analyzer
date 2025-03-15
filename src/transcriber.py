"""
Module for transcribing audio using Whisper API via Groq.
"""

import os
import json
import tempfile
import subprocess
import shutil
import time
from pathlib import Path
from groq import Groq
from pydub import AudioSegment

# Try to load rich for better UI
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
    from rich.panel import Panel
    rich_available = True
except ImportError:
    rich_available = False

# Try to load tqdm for progress bars
try:
    from tqdm import tqdm
    tqdm_available = True
except ImportError:
    tqdm_available = False

# Set up Rich console
console = Console() if rich_available else None

# Import dotenv for loading environment variables
try:
    from dotenv import load_dotenv
    dotenv_available = True
except ImportError:
    dotenv_available = False

# Maximum file size for Groq API in bytes (25MB)
MAX_FILE_SIZE = 25 * 1024 * 1024

# Default chunk duration in milliseconds (5 minutes)
DEFAULT_CHUNK_DURATION = 5 * 60 * 1000

def load_api_key():
    """
    Load Groq API key from .env file or environment variables.
    
    Returns:
        str: API key or None if not found
    """
    # Try to load from .env file if dotenv is available
    if dotenv_available:
        # Look for .env in current directory and then in project root
        env_paths = [
            '.env',  # Current directory
            Path(__file__).resolve().parent.parent / '.env'  # Project root
        ]
        
        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path)
                break
    
    # Get API key from environment variable
    api_key = os.environ.get("GROQ_API_KEY")
    return api_key

def get_file_size(file_path):
    """
    Get the size of a file in bytes.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        int: Size of the file in bytes
    """
    return os.path.getsize(file_path)

def find_ffmpeg_tools():
    """
    Find ffmpeg and ffprobe executables in the system or project directory.
    
    Returns:
        tuple: (ffmpeg_path, ffprobe_path) or (None, None) if not found
    """
    ffmpeg_path = None
    ffprobe_path = None
    
    # Check environment variables
    if 'FFMPEG_PATH' in os.environ and os.path.exists(os.environ['FFMPEG_PATH']):
        ffmpeg_path = os.environ['FFMPEG_PATH']
    
    if 'FFPROBE_PATH' in os.environ and os.path.exists(os.environ['FFPROBE_PATH']):
        ffprobe_path = os.environ['FFPROBE_PATH']
        
    if ffmpeg_path and ffprobe_path:
        return ffmpeg_path, ffprobe_path
    
    # Common names for the executables
    ffmpeg_names = ['ffmpeg', 'ffmpeg.exe']
    ffprobe_names = ['ffprobe', 'ffprobe.exe']
    
    # Check in PATH
    for name in ffmpeg_names:
        if not ffmpeg_path and shutil.which(name):
            ffmpeg_path = shutil.which(name)
    
    for name in ffprobe_names:
        if not ffprobe_path and shutil.which(name):
            ffprobe_path = shutil.which(name)
    
    # Check in common locations
    common_locations = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),  # Project root
        os.path.join(os.path.dirname(os.path.abspath(__file__))),  # src directory
        os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin'),  # User's ffmpeg directory
        '/usr/bin',
        '/usr/local/bin',
        'C:\\ffmpeg\\bin',
        os.getcwd()  # Current working directory
    ]
    
    for location in common_locations:
        for name in ffmpeg_names:
            potential_path = os.path.join(location, name)
            if not ffmpeg_path and os.path.exists(potential_path):
                ffmpeg_path = potential_path
        
        for name in ffprobe_names:
            potential_path = os.path.join(location, name)
            if not ffprobe_path and os.path.exists(potential_path):
                ffprobe_path = potential_path
        
        if ffmpeg_path and ffprobe_path:
            break
            
    if ffmpeg_path:
        if rich_available:
            console.print(f"Found ffmpeg at: [green]{ffmpeg_path}[/green]")
        else:
            print(f"Found ffmpeg at: {ffmpeg_path}")
        
    if ffprobe_path:
        if rich_available:
            console.print(f"Found ffprobe at: [green]{ffprobe_path}[/green]")
        else:
            print(f"Found ffprobe at: {ffprobe_path}")
    
    return ffmpeg_path, ffprobe_path

def split_audio_file_with_ffmpeg(audio_file, max_size=MAX_FILE_SIZE, chunk_duration=DEFAULT_CHUNK_DURATION):
    """
    Split audio file into chunks using ffmpeg.
    
    Args:
        audio_file (str): Path to the audio file
        max_size (int): Maximum size of each chunk in bytes
        chunk_duration (int): Target duration for each chunk in milliseconds
        
    Returns:
        list: List of paths to the created chunks
    """
    try:
        # First get the audio file duration using ffprobe
        ffmpeg_path, ffprobe_path = find_ffmpeg_tools()
        
        if not ffprobe_path:
            if rich_available:
                console.print("[bold red]Error:[/bold red] ffprobe not found. Cannot determine audio duration.")
            else:
                print("Error: ffprobe not found. Cannot determine audio duration.")
            return None
            
        if not ffmpeg_path:
            if rich_available:
                console.print("[bold red]Error:[/bold red] ffmpeg not found. Cannot split audio file.")
            else:
                print("Error: ffmpeg not found. Cannot split audio file.")
            return None
        
        # Get duration using ffprobe
        if rich_available:
            console.print(f"Using ffmpeg at: [green]{ffmpeg_path}[/green]")
        else:
            print(f"Using ffmpeg at: {ffmpeg_path}")
            
        command = [
            ffprobe_path, 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_file
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            if rich_available:
                console.print(f"[bold red]Error:[/bold red] Failed to get audio duration: {result.stderr}")
            else:
                print(f"Error: Failed to get audio duration: {result.stderr}")
            return None
            
        duration = float(result.stdout.strip())
        
        if rich_available:
            console.print(f"Audio duration: [green]{duration:.2f}[/green] seconds")
        else:
            print(f"Audio duration: {duration:.2f} seconds")
        
        # Calculate number of chunks
        chunk_duration_seconds = chunk_duration / 1000
        num_chunks = max(1, int(duration / chunk_duration_seconds) + (1 if duration % chunk_duration_seconds > 0 else 0))
        
        if rich_available:
            console.print(f"Splitting into approximately [green]{num_chunks}[/green] chunks...")
        else:
            print(f"Splitting into approximately {num_chunks} chunks...")
        
        # Create a temporary directory for chunks
        temp_dir = tempfile.mkdtemp()
        chunks = []
        
        # Set up progress tracking
        if rich_available:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold green]Creating chunk {task.fields[chunk_num]}/{task.fields[total_chunks]}..."),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
            )
            task = progress.add_task("[green]Splitting audio...", total=num_chunks, chunk_num=0, total_chunks=num_chunks)
            with progress:
                for i in range(num_chunks):
                    progress.update(task, advance=0, chunk_num=i+1)
                    
                    # Calculate start and end times for this chunk
                    start_time = i * chunk_duration_seconds
                    
                    # Create output path for this chunk
                    output_path = os.path.join(temp_dir, f"chunk_{i}.mp3")
                    
                    # Build ffmpeg command
                    command = [
                        ffmpeg_path,
                        "-i", audio_file,
                        "-ss", str(start_time),
                        "-t", str(chunk_duration_seconds),
                        "-acodec", "libmp3lame",
                        "-ab", "128k",
                        "-ar", "44100",
                        "-y",  # Overwrite output files without asking
                        output_path
                    ]
                    
                    # Run ffmpeg
                    subprocess.run(command, capture_output=True)
                    
                    # Check if the chunk was created
                    if os.path.exists(output_path):
                        chunk_size = get_file_size(output_path) / (1024 * 1024)  # Size in MB
                        console.print(f"Created chunk {i+1}: [green]{output_path}[/green] ({chunk_size:.2f} MB)")
                        chunks.append(output_path)
                    else:
                        console.print(f"[bold yellow]Warning:[/bold yellow] Failed to create chunk {i+1}")
                    
                    progress.update(task, advance=1)
        else:
            # Use tqdm if available, otherwise regular loop
            iterator = tqdm(range(num_chunks), desc="Splitting audio") if tqdm_available else range(num_chunks)
            
            for i in iterator:
                # Calculate start and end times for this chunk
                start_time = i * chunk_duration_seconds
                
                # Create output path for this chunk
                output_path = os.path.join(temp_dir, f"chunk_{i}.mp3")
                
                # Build ffmpeg command
                command = [
                    ffmpeg_path,
                    "-i", audio_file,
                    "-ss", str(start_time),
                    "-t", str(chunk_duration_seconds),
                    "-acodec", "libmp3lame",
                    "-ab", "128k",
                    "-ar", "44100",
                    "-y",  # Overwrite output files without asking
                    output_path
                ]
                
                print(f"Creating chunk {i+1}/{num_chunks}...")
                
                # Run ffmpeg
                subprocess.run(command, capture_output=True)
                
                # Check if the chunk was created
                if os.path.exists(output_path):
                    chunk_size = get_file_size(output_path) / (1024 * 1024)  # Size in MB
                    print(f"Created chunk {i+1}: {output_path} ({chunk_size:.2f} MB)")
                    chunks.append(output_path)
                else:
                    print(f"Warning: Failed to create chunk {i+1}")
        
        if chunks:
            if rich_available:
                console.print(f"Split audio into [green]{len(chunks)}[/green] chunks")
            else:
                print(f"Split audio into {len(chunks)} chunks")
            return chunks
        else:
            if rich_available:
                console.print("[bold red]Error:[/bold red] Failed to create any chunks")
            else:
                print("Error: Failed to create any chunks")
            return None
            
    except Exception as e:
        if rich_available:
            console.print(f"[bold red]Error splitting audio file:[/bold red] {str(e)}")
        else:
            print(f"Error splitting audio file: {str(e)}")
        return None

def split_audio_file(audio_file, max_size=MAX_FILE_SIZE, chunk_duration=DEFAULT_CHUNK_DURATION):
    """
    Split an audio file into smaller chunks.
    
    Args:
        audio_file (str): Path to the audio file
        max_size (int): Maximum file size in bytes
        chunk_duration (int): Duration of each chunk in milliseconds
        
    Returns:
        list: List of paths to the chunk files
    """
    try:
        # Check if file needs splitting
        file_size = get_file_size(audio_file)
        if file_size <= max_size:
            print(f"Audio file is small enough ({file_size / (1024*1024):.2f} MB), no need to split")
            return [audio_file]
            
        print(f"Audio file is too large ({file_size / (1024*1024):.2f} MB), splitting into chunks...")
        
        # Try using ffmpeg directly first (more reliable)
        ffmpeg_chunks = split_audio_file_with_ffmpeg(audio_file, max_size, chunk_duration)
        if ffmpeg_chunks and len(ffmpeg_chunks) > 1:
            return ffmpeg_chunks
            
        # If ffmpeg direct method failed, try with pydub
        print("Trying to split with pydub...")
        
        # Set ffmpeg paths for pydub
        ffmpeg_path, ffprobe_path = find_ffmpeg_tools()
        if ffmpeg_path:
            AudioSegment.converter = ffmpeg_path
        if ffprobe_path:
            AudioSegment.ffprobe = ffprobe_path
            
        # Load the audio file
        audio = AudioSegment.from_file(audio_file)
        total_duration = len(audio)
        
        # Create a temporary directory for chunks
        temp_dir = tempfile.mkdtemp()
        chunk_files = []
        
        # Split the audio into chunks
        for i, start in enumerate(range(0, total_duration, chunk_duration)):
            end = min(start + chunk_duration, total_duration)
            chunk = audio[start:end]
            
            # Save the chunk to a temporary file
            chunk_file = os.path.join(temp_dir, f"chunk_{i}.mp3")
            chunk.export(chunk_file, format="mp3", bitrate="64k")
            
            # Check if the chunk is still too large
            if get_file_size(chunk_file) > max_size:
                print(f"Warning: Chunk {i} is still too large, reducing quality further...")
                # Try with even lower quality
                chunk.export(chunk_file, format="mp3", bitrate="32k", parameters=["-ac", "1"])
                
                # If still too large, skip this chunk
                if get_file_size(chunk_file) > max_size:
                    print(f"Warning: Chunk {i} is still too large even with reduced quality, skipping")
                    os.remove(chunk_file)
                    continue
            
            chunk_files.append(chunk_file)
            print(f"Created chunk {i+1}: {chunk_file} ({get_file_size(chunk_file) / (1024*1024):.2f} MB)")
        
        print(f"Split audio into {len(chunk_files)} chunks")
        return chunk_files
    
    except Exception as e:
        print(f"Error splitting audio file: {e}")
        return [audio_file]  # Return original file if splitting fails

def transcribe_audio_chunk(audio_file, client, model="whisper-large-v3"):
    """
    Transcribe a single audio chunk.
    
    Args:
        audio_file (str): Path to the audio file
        client: Groq client instance
        model (str): Whisper model to use
        
    Returns:
        dict or str: Transcribed text with timestamps if available, or plain text
    """
    try:
        # Check file size
        file_size = get_file_size(audio_file)
        print(f"Transcribing file of size: {file_size / (1024*1024):.2f} MB")
        
        if file_size > MAX_FILE_SIZE:
            print(f"Warning: File size ({file_size / (1024*1024):.2f} MB) exceeds Groq API limit ({MAX_FILE_SIZE / (1024*1024)} MB)")
            return None
        
        # Open the audio file
        with open(audio_file, "rb") as file:
            file_content = file.read()
            file_name = os.path.basename(audio_file)
            
            # Create a transcription of the audio file with timestamps
            transcription = client.audio.transcriptions.create(
                file=(file_name, file_content),
                model=model,
                response_format="verbose_json",  # Request verbose JSON format with timestamps
                timestamp_granularities=["segment"]  # Explicitly request segment-level timestamps
            )
        
        # Fix the response handling logic to prioritize checking for timestamps
        if isinstance(transcription, dict) and 'segments' in transcription:
            # Direct dictionary response with timestamps
            transcript_data = transcription
            print(f"Chunk transcription completed with timestamps: {len(transcript_data.get('text', ''))} characters (JSON format)")
            return transcript_data
        elif hasattr(transcription, 'segments') and hasattr(transcription, 'text'):
            # Object with segments - convert to dictionary
            segment_list = transcription.segments
            if hasattr(segment_list, 'to_dict'):
                segment_list = segment_list.to_dict()
            elif hasattr(segment_list, 'to_list'):
                segment_list = segment_list.to_list()
                
            transcript_data = {
                'text': transcription.text,
                'segments': segment_list
            }
            print(f"Chunk transcription completed with timestamps: {len(transcript_data['text'])} characters (object format)")
            return transcript_data
        elif hasattr(transcription, 'text'):
            # Just text attribute without segments
            transcript_text = transcription.text
            print(f"Chunk transcription completed: {len(transcript_text)} characters (text format)")
            return transcript_text
        elif isinstance(transcription, str):
            # Direct string response
            transcript_text = transcription
            print(f"Chunk transcription completed: {len(transcript_text)} characters (string format)")
            return transcript_text
        else:
            # Try to convert to string or extract text in some other way
            try:
                # Try to get json representation first
                if hasattr(transcription, 'model_dump_json'):
                    json_data = json.loads(transcription.model_dump_json())
                    if 'text' in json_data and 'segments' in json_data:
                        print(f"Chunk transcription completed with timestamps: {len(json_data['text'])} characters (converted JSON)")
                        return json_data
            except Exception as conversion_error:
                print(f"Error converting response to JSON: {conversion_error}")
                
            # Fall back to string conversion
            transcript_text = str(transcription)
            print(f"Chunk transcription completed: {len(transcript_text)} characters (converted format)")
            return transcript_text
    
    except Exception as e:
        print(f"Error transcribing chunk {audio_file}: {e}")
        return None

def transcribe_audio(audio_file, api_key=None, model="whisper-large-v3"):
    """
    Transcribe audio file using Whisper API.
    
    Args:
        audio_file (str): Path to the audio file
        api_key (str): API key for Groq (optional, can be loaded from .env)
        model (str): Whisper model to use
        
    Returns:
        dict or str: Transcript as dictionary with timestamps (if available) or string
    """
    try:
        # Load API key if not provided
        if not api_key:
            api_key = load_api_key()
            
        if not api_key:
            if rich_available:
                console.print("[bold red]Error:[/bold red] No API key provided. Set GROQ_API_KEY in environment or .env file.")
            else:
                print("Error: No API key provided. Set GROQ_API_KEY in environment or .env file.")
            return None
            
        # Check if file exists
        if not os.path.exists(audio_file):
            if rich_available:
                console.print(f"[bold red]Error:[/bold red] Audio file not found: {audio_file}")
            else:
                print(f"Error: Audio file not found: {audio_file}")
            return None
            
        # Get file size
        file_size = get_file_size(audio_file)
        file_size_mb = file_size / (1024 * 1024)  # Convert to MB for display
        
        if rich_available:
            console.print(f"Audio file size: [green]{file_size_mb:.2f} MB[/green]")
        else:
            print(f"Audio file size: {file_size_mb:.2f} MB")
            
        # Initialize Groq client
        client = Groq(api_key=api_key)
        
        # Check if file is too large
        if file_size > MAX_FILE_SIZE:
            # Split file into chunks
            if rich_available:
                console.print(f"Audio file is too large ([red]{file_size_mb:.2f} MB[/red]), splitting into chunks...")
            else:
                print(f"Audio file is too large ({file_size_mb:.2f} MB), splitting into chunks...")
                
            chunks = split_audio_file_with_ffmpeg(audio_file)
            if not chunks:
                if rich_available:
                    console.print("[bold red]Error:[/bold red] Failed to split audio file")
                else:
                    print("Error: Failed to split audio file")
                return None
                
            # Transcribe each chunk
            chunk_transcripts = []
            combined_text = ""
            combined_segments = []
            time_offset = 0
            
            if rich_available:
                console.print(f"Transcribing [green]{len(chunks)}[/green] audio chunks...")
                
                # Setup progress for transcription
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold green]Transcribing chunk {task.fields[chunk_num]}/{task.fields[total_chunks]}..."),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeRemainingColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("[green]Transcribing...", total=len(chunks), chunk_num=0, total_chunks=len(chunks))
                    
                    for i, chunk in enumerate(chunks):
                        progress.update(task, advance=0, chunk_num=i+1)
                        
                        console.print(f"Transcribing chunk {i+1}/{len(chunks)}...")
                        chunk_size = get_file_size(chunk) / (1024 * 1024)  # Size in MB
                        console.print(f"Transcribing file of size: [green]{chunk_size:.2f} MB[/green]")
                        
                        # Wait a bit to avoid rate limits
                        if i > 0:
                            wait_time = 2
                            console.print(f"Waiting [yellow]{wait_time}[/yellow] seconds before next API call...")
                            time.sleep(wait_time)
                        
                        # Transcribe chunk
                        chunk_transcript = transcribe_audio_chunk(chunk, client, model)
                        
                        if chunk_transcript:
                            # Determine duration of this chunk to calculate next offset
                            duration = 0
                            is_object = isinstance(chunk_transcript, dict)
                            
                            if is_object and 'segments' in chunk_transcript and chunk_transcript['segments']:
                                # Get duration from the end time of the last segment
                                if isinstance(chunk_transcript['segments'][-1], dict) and 'end' in chunk_transcript['segments'][-1]:
                                    duration = chunk_transcript['segments'][-1]['end']
                                    console.print(f"Chunk duration: [green]{duration:.2f}[/green] seconds, new offset: [green]{time_offset + duration:.2f}[/green]")
                                    
                                    # Adjust segments with time offset
                                    for segment in chunk_transcript['segments']:
                                        if isinstance(segment, dict):
                                            if 'start' in segment:
                                                segment['start'] += time_offset
                                            if 'end' in segment:
                                                segment['end'] += time_offset
                                    
                                    # Add adjusted segments to combined segments
                                    combined_segments.extend(chunk_transcript['segments'])
                            
                            chunk_transcripts.append(chunk_transcript)
                            
                            # Extract text
                            chunk_text = chunk_transcript['text'] if is_object and 'text' in chunk_transcript else str(chunk_transcript)
                            combined_text += chunk_text
                            
                            char_count = len(chunk_text)
                            console.print(f"Chunk transcription completed: [green]{char_count}[/green] characters{'with timestamps' if is_object else ''}")
                            
                            # Update time offset for next chunk
                            if is_object and duration > 0:
                                time_offset += duration
                        else:
                            console.print(f"[bold yellow]Warning:[/bold yellow] Failed to transcribe chunk {i+1}")
                            
                        progress.update(task, advance=1)
            else:
                # Use tqdm if available, otherwise regular loop
                iterator = tqdm(enumerate(chunks), total=len(chunks), desc="Transcribing chunks") if tqdm_available else enumerate(chunks)
                
                for i, chunk in iterator:
                    print(f"Transcribing chunk {i+1}/{len(chunks)}...")
                    chunk_size = get_file_size(chunk) / (1024 * 1024)  # Size in MB
                    print(f"Transcribing file of size: {chunk_size:.2f} MB")
                    
                    # Wait a bit to avoid rate limits
                    if i > 0:
                        wait_time = 2
                        print(f"Waiting {wait_time} seconds before next API call...")
                        time.sleep(wait_time)
                    
                    # Transcribe chunk
                    chunk_transcript = transcribe_audio_chunk(chunk, client, model)
                    
                    if chunk_transcript:
                        # Determine duration of this chunk to calculate next offset
                        duration = 0
                        is_object = isinstance(chunk_transcript, dict)
                        
                        if is_object and 'segments' in chunk_transcript and chunk_transcript['segments']:
                            # Get duration from the end time of the last segment
                            if isinstance(chunk_transcript['segments'][-1], dict) and 'end' in chunk_transcript['segments'][-1]:
                                duration = chunk_transcript['segments'][-1]['end']
                                print(f"Chunk duration: {duration:.2f} seconds, new offset: {time_offset + duration:.2f}")
                                
                                # Adjust segments with time offset
                                for segment in chunk_transcript['segments']:
                                    if isinstance(segment, dict):
                                        if 'start' in segment:
                                            segment['start'] += time_offset
                                        if 'end' in segment:
                                            segment['end'] += time_offset
                                
                                # Add adjusted segments to combined segments
                                combined_segments.extend(chunk_transcript['segments'])
                        
                        chunk_transcripts.append(chunk_transcript)
                        
                        # Extract text
                        chunk_text = chunk_transcript['text'] if is_object and 'text' in chunk_transcript else str(chunk_transcript)
                        combined_text += chunk_text
                        
                        char_count = len(chunk_text)
                        print(f"Chunk transcription completed: {char_count} characters{'with timestamps' if is_object else ''}")
                        
                        # Update time offset for next chunk
                        if is_object and duration > 0:
                            time_offset += duration
                    else:
                        print(f"Warning: Failed to transcribe chunk {i+1}")
            
            # Clean up chunks
            for chunk in chunks:
                if os.path.exists(chunk):
                    os.remove(chunk)
            
            # Clean up temp directory
            temp_dir = os.path.dirname(chunks[0]) if chunks else None
            if temp_dir and os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            
            # Check if we should return a structured object with timestamps
            if combined_segments:
                result = {
                    'text': combined_text,
                    'segments': combined_segments
                }
            else:
                result = combined_text
            
            char_count = len(combined_text)
            if rich_available:
                console.print(f"Transcription completed: [green]{char_count}[/green] characters from [green]{len(chunks)}[/green] chunks")
            else:
                print(f"Transcription completed: {char_count} characters from {len(chunks)} chunks")
            
            return result
        else:
            # Transcribe the entire file at once
            if rich_available:
                with console.status("[bold green]Transcribing audio...", spinner="dots"):
                    transcript = transcribe_audio_chunk(audio_file, client, model)
            else:
                print("Transcribing audio...")
                transcript = transcribe_audio_chunk(audio_file, client, model)
            
            if transcript:
                if isinstance(transcript, dict) and 'text' in transcript:
                    char_count = len(transcript['text'])
                    has_timestamps = 'segments' in transcript and transcript['segments']
                    if rich_available:
                        console.print(f"Transcription completed: [green]{char_count}[/green] characters" + 
                                      (" [green]with timestamps[/green]" if has_timestamps else ""))
                    else:
                        print(f"Transcription completed: {char_count} characters" +
                              (" with timestamps" if has_timestamps else ""))
                else:
                    char_count = len(str(transcript))
                    if rich_available:
                        console.print(f"Transcription completed: [green]{char_count}[/green] characters")
                    else:
                        print(f"Transcription completed: {char_count} characters")
                
                return transcript
            else:
                if rich_available:
                    console.print("[bold red]Error:[/bold red] Failed to transcribe audio")
                else:
                    print("Error: Failed to transcribe audio")
                return None
                
    except Exception as e:
        if rich_available:
            console.print(f"[bold red]Error transcribing audio:[/bold red] {str(e)}")
        else:
            print(f"Error transcribing audio: {str(e)}")
        return None

def save_transcript(transcript, output_file):
    """
    Save transcript to a file.
    
    Args:
        transcript (str or dict): Transcript text or dictionary with text and timestamps
        output_file (str): Path to output file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Check if we have a dictionary with text and timestamps
        if isinstance(transcript, dict) and 'text' in transcript:
            # If output file ends with .txt, save just the text
            if output_file.endswith('.txt'):
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(transcript['text'])
                print(f"Transcript text saved to: {output_file}")
                
                # Also save the full transcript with timestamps to a JSON file
                json_file = output_file.replace('.txt', '.json')
                
                # Ensure all data is JSON serializable
                json_safe_transcript = transcript.copy()
                
                # Handle potential non-serializable objects in segments
                if 'segments' in json_safe_transcript:
                    # Convert any special objects to dictionaries
                    if isinstance(json_safe_transcript['segments'], list):
                        for i, segment in enumerate(json_safe_transcript['segments']):
                            if not isinstance(segment, dict):
                                if hasattr(segment, 'to_dict'):
                                    json_safe_transcript['segments'][i] = segment.to_dict()
                                elif hasattr(segment, '__dict__'):
                                    json_safe_transcript['segments'][i] = segment.__dict__
                
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(json_safe_transcript, f, indent=2, default=str)
                print(f"Transcript with timestamps saved to: {json_file}")
            else:
                # For other file types, save the entire transcript dictionary
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(transcript, f, indent=2, default=str)
                print(f"Transcript with timestamps saved to: {output_file}")
        else:
            # Save plain text transcript
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(str(transcript))
            print(f"Transcript saved to: {output_file}")
        
        return True
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return False

def load_transcript(transcript_file):
    """
    Load transcript from a local file.
    
    Args:
        transcript_file (str): Path to the transcript file
        
    Returns:
        str or dict: Transcript text or dictionary with text and timestamps
    """
    try:
        if not os.path.exists(transcript_file):
            print(f"Error: Transcript file not found: {transcript_file}")
            return None
            
        print(f"Loading transcript from: {transcript_file}")
        
        # Check if this is a JSON file with timestamps
        if transcript_file.endswith('.json'):
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_data = json.load(f)
                    
                # Validate that it's a transcript with required fields
                if isinstance(transcript_data, dict) and 'text' in transcript_data:
                    print(f"Loaded transcript with timestamps ({len(transcript_data['text'])} characters)")
                    return transcript_data
                else:
                    print("Warning: JSON file doesn't appear to be a valid transcript with timestamps")
                    # Try to extract text if possible
                    if isinstance(transcript_data, dict) and any(key for key in transcript_data if isinstance(transcript_data[key], str)):
                        # Find the longest string field in the JSON and use that as transcript
                        text_field = max(
                            [(k, len(v)) for k, v in transcript_data.items() if isinstance(v, str)],
                            key=lambda x: x[1]
                        )[0]
                        print(f"Using field '{text_field}' as transcript text")
                        return transcript_data[text_field]
            except json.JSONDecodeError:
                print("Warning: Failed to parse JSON file, trying as plain text")
        
        # Load as plain text
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
            
        print(f"Loaded plain text transcript ({len(transcript_text)} characters)")
        return transcript_text
        
    except Exception as e:
        print(f"Error loading transcript: {e}")
        return None

def find_existing_transcript(video_id, output_dir="output"):
    """
    Find an existing transcript file for a video ID.
    
    Args:
        video_id (str): YouTube video ID
        output_dir (str): Directory to search in
        
    Returns:
        str or None: Path to transcript file if found, None otherwise
    """
    if not os.path.exists(output_dir):
        return None
        
    # Look for transcript files matching the pattern
    transcript_pattern = f"transcript_{video_id}_*.json"
    matching_json_files = list(Path(output_dir).glob(transcript_pattern))
    
    if matching_json_files:
        # Use the most recent JSON file (with timestamps)
        latest_file = max(matching_json_files, key=lambda x: x.stat().st_mtime)
        return str(latest_file)
    
    # If no JSON files, try plain text
    transcript_pattern = f"transcript_{video_id}_*.txt"
    matching_txt_files = list(Path(output_dir).glob(transcript_pattern))
    
    if matching_txt_files:
        # Use the most recent text file
        latest_file = max(matching_txt_files, key=lambda x: x.stat().st_mtime)
        return str(latest_file)
    
    return None 