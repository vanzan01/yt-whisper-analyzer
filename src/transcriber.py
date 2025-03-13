"""
Module for transcribing audio using Whisper API via Groq.
"""

import os
import json
import tempfile
import subprocess
import shutil
from pathlib import Path
from groq import Groq
from pydub import AudioSegment

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
        os.path.join(os.path.expanduser('~'), 'bin'),  # User's bin directory
        '/usr/local/bin',  # Common Unix location
        '/usr/bin',        # Common Unix location
        'C:\\ffmpeg\\bin',  # Common Windows location
        'D:\\ffmpeg\\bin',  # Alternative Windows location
    ]
    
    # Add current working directory
    common_locations.append(os.getcwd())
    
    for location in common_locations:
        if os.path.exists(location):
            # Check for ffmpeg
            if not ffmpeg_path:
                for name in ffmpeg_names:
                    ffmpeg_candidate = os.path.join(location, name)
                    if os.path.exists(ffmpeg_candidate) and os.access(ffmpeg_candidate, os.X_OK):
                        ffmpeg_path = ffmpeg_candidate
                        break
            
            # Check for ffprobe
            if not ffprobe_path:
                for name in ffprobe_names:
                    ffprobe_candidate = os.path.join(location, name)
                    if os.path.exists(ffprobe_candidate) and os.access(ffprobe_candidate, os.X_OK):
                        ffprobe_path = ffprobe_candidate
                        break
    
    # Print debug info
    if ffmpeg_path:
        print(f"Found ffmpeg at: {ffmpeg_path}")
    else:
        print("Warning: ffmpeg not found. Audio splitting may not work correctly.")
        
    if ffprobe_path:
        print(f"Found ffprobe at: {ffprobe_path}")
    else:
        print("Warning: ffprobe not found. Audio duration detection may not work correctly.")
    
    return ffmpeg_path, ffprobe_path

def split_audio_file_with_ffmpeg(audio_file, max_size=MAX_FILE_SIZE, chunk_duration=DEFAULT_CHUNK_DURATION):
    """
    Split an audio file into smaller chunks using ffmpeg directly.
    
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
        
        # Find ffmpeg
        ffmpeg_path, ffprobe_path = find_ffmpeg_tools()
        if not ffmpeg_path:
            print("Error: ffmpeg not found. Cannot split audio file.")
            return [audio_file]
            
        print(f"Using ffmpeg at: {ffmpeg_path}")
        
        # Create a temporary directory for chunks
        temp_dir = tempfile.mkdtemp()
        chunk_files = []
        
        # Get audio duration using ffprobe if available
        total_duration_sec = None
        if ffprobe_path:
            try:
                cmd = [
                    ffprobe_path,
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    audio_file
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    total_duration_sec = float(result.stdout.strip())
                    print(f"Audio duration: {total_duration_sec:.2f} seconds")
            except Exception as e:
                print(f"Error getting audio duration: {e}")
        
        # If we couldn't get the duration, estimate based on file size
        if not total_duration_sec:
            # Rough estimate: 1MB ~ 1 minute for MP3 at moderate quality
            estimated_minutes = file_size / (1024*1024)
            total_duration_sec = estimated_minutes * 60
            print(f"Estimated audio duration: {total_duration_sec:.2f} seconds (based on file size)")
        
        # Calculate chunk duration in seconds
        chunk_duration_sec = chunk_duration / 1000  # Convert to seconds
        
        # Calculate number of chunks needed to cover the entire audio
        num_chunks = max(2, int(total_duration_sec / chunk_duration_sec) + 1)
        print(f"Splitting into approximately {num_chunks} chunks...")
        
        for i in range(num_chunks):
            chunk_file = os.path.join(temp_dir, f"chunk_{i}.mp3")
            
            # Calculate start time and duration for this chunk
            start_time = i * chunk_duration_sec
            
            # For the last chunk, make sure we don't exceed the total duration
            if total_duration_sec and start_time >= total_duration_sec:
                print(f"Reached end of audio at chunk {i}")
                break
                
            # Build ffmpeg command
            cmd = [
                ffmpeg_path,
                "-y",  # Overwrite output files
                "-i", audio_file,
                "-ss", str(start_time),  # Start time
                "-t", str(chunk_duration_sec),  # Duration
                "-acodec", "libmp3lame",
                "-ab", "128k",  # Lower bitrate to reduce file size
                "-ac", "1",  # Mono audio
                "-ar", "22050",  # Lower sample rate
                chunk_file
            ]
            
            # Run ffmpeg
            print(f"Creating chunk {i+1}/{num_chunks}...")
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Check if the chunk was created and is not empty
            if os.path.exists(chunk_file) and os.path.getsize(chunk_file) > 0:
                chunk_size = get_file_size(chunk_file) / (1024*1024)
                chunk_files.append(chunk_file)
                print(f"Created chunk {i+1}: {chunk_file} ({chunk_size:.2f} MB)")
            else:
                print(f"Chunk {i+1} is empty or was not created, likely reached end of file")
                break
        
        print(f"Split audio into {len(chunk_files)} chunks")
        return chunk_files
    
    except Exception as e:
        print(f"Error splitting audio file with ffmpeg: {e}")
        return [audio_file]  # Return original file if splitting fails

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
        str: Transcribed text or None if transcription failed
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
            
            # Create a transcription of the audio file
            transcription = client.audio.transcriptions.create(
                file=(file_name, file_content),
                model=model,
                response_format="text"
            )
        
        # Handle different response types from the API
        if hasattr(transcription, 'text'):
            # Object with text attribute
            transcript_text = transcription.text
        elif isinstance(transcription, str):
            # Direct string response
            transcript_text = transcription
        else:
            # Try to convert to string or extract text in some other way
            transcript_text = str(transcription)
            
        print(f"Chunk transcription completed: {len(transcript_text)} characters")
        return transcript_text
    
    except Exception as e:
        print(f"Error transcribing chunk {audio_file}: {e}")
        return None

def transcribe_audio(audio_file, api_key=None, model="whisper-large-v3"):
    """
    Transcribe audio using Whisper API via Groq.
    
    Args:
        audio_file (str): Path to the audio file
        api_key (str, optional): Groq API key. If None, will try to load from environment
        model (str, optional): Whisper model to use. Defaults to "whisper-large-v3"
        
    Returns:
        str: Transcribed text
    """
    # Load API key if not provided
    if not api_key:
        api_key = load_api_key()
        if not api_key:
            raise ValueError("No API key provided. Please set GROQ_API_KEY environment variable or use --api_key parameter.")
    
    # Initialize Groq client
    client = Groq(api_key=api_key)
    
    # Check if file needs splitting
    file_size = get_file_size(audio_file)
    if file_size > MAX_FILE_SIZE:
        print(f"Audio file size: {file_size / (1024*1024):.2f} MB")
        # Split audio into chunks
        chunk_files = split_audio_file(audio_file, MAX_FILE_SIZE, DEFAULT_CHUNK_DURATION)
        
        if len(chunk_files) == 1 and chunk_files[0] == audio_file:
            # Splitting failed, try to reduce quality
            print("Splitting failed, trying to reduce audio quality...")
            try:
                ffmpeg_path, _ = find_ffmpeg_tools()
                if ffmpeg_path:
                    temp_file = os.path.join(os.path.dirname(audio_file), "reduced_quality.mp3")
                    cmd = [
                        ffmpeg_path,
                        "-y",
                        "-i", audio_file,
                        "-acodec", "libmp3lame",
                        "-ab", "32k",  # Very low bitrate
                        "-ac", "1",    # Mono
                        "-ar", "16000", # Lower sample rate
                        temp_file
                    ]
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                        reduced_size = get_file_size(temp_file) / (1024*1024)
                        print(f"Reduced audio file size: {reduced_size:.2f} MB")
                        if reduced_size <= MAX_FILE_SIZE:
                            print("Successfully reduced file size, using reduced quality audio")
                            audio_file = temp_file
                            return transcribe_audio_chunk(audio_file, client, model)
                        else:
                            print("File still too large after quality reduction, trying to split again")
                            chunk_files = split_audio_file(temp_file, MAX_FILE_SIZE, DEFAULT_CHUNK_DURATION)
            except Exception as e:
                print(f"Error reducing audio quality: {e}")
        
        # Transcribe each chunk
        print(f"Transcribing {len(chunk_files)} audio chunks...")
        transcripts = []
        successful_chunks = 0
        
        for i, chunk_file in enumerate(chunk_files):
            try:
                print(f"Transcribing chunk {i+1}/{len(chunk_files)}...")
                chunk_transcript = transcribe_audio_chunk(chunk_file, client, model)
                if chunk_transcript:
                    transcripts.append(chunk_transcript)
                    print(f"Chunk transcription completed: {len(chunk_transcript)} characters")
                    successful_chunks += 1
                else:
                    print(f"Warning: Empty transcript for chunk {i+1}")
            except Exception as e:
                print(f"Error transcribing chunk {i+1}: {e}")
        
        # Clean up temporary files
        try:
            temp_dir = os.path.dirname(chunk_files[0])
            if os.path.exists(temp_dir) and temp_dir != os.path.dirname(audio_file):
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")
        
        # Combine transcripts
        full_transcript = " ".join(transcripts)
        print(f"Transcription completed: {len(full_transcript)} characters from {successful_chunks} chunks")
        
        if successful_chunks == 0:
            raise ValueError("All chunks failed to transcribe. Please check your API key and network connection.")
        
        if successful_chunks < len(chunk_files):
            print(f"Warning: Only {successful_chunks}/{len(chunk_files)} chunks were successfully transcribed")
            
        return full_transcript
    else:
        # File is small enough, transcribe directly
        print(f"Audio file is small enough ({file_size / (1024*1024):.2f} MB), transcribing directly")
        return transcribe_audio_chunk(audio_file, client, model)
        
def save_transcript(transcript, output_file):
    """
    Save transcript to a file.
    
    Args:
        transcript (str): Transcript text
        output_file (str): Path to output file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        print(f"Transcript saved to: {output_file}")
        return True
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return False 