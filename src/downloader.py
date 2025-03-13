"""
Module for downloading audio from YouTube videos.
"""

import os
import re
import time
import random
import subprocess
import shutil
from urllib.parse import urlparse, parse_qs

# Maximum number of retries for downloading
MAX_RETRIES = 3
# Delay between retries (in seconds)
RETRY_DELAY = [1, 3, 5]  # Progressive backoff

def extract_video_id(url):
    """
    Extract the YouTube video ID from various URL formats.
    
    Args:
        url (str): YouTube URL in any format
        
    Returns:
        str: YouTube video ID or None if not found
    """
    if not url:
        return None
    
    # Check if the input is already a video ID (no slashes or special chars)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    # Handle youtube.com URLs
    parsed_url = urlparse(url)
    if 'youtube.com' in parsed_url.netloc:
        query_params = parse_qs(parsed_url.query)
        if 'v' in query_params:
            return query_params['v'][0]
    
    # Handle youtu.be URLs
    if 'youtu.be' in parsed_url.netloc:
        return parsed_url.path.lstrip('/')
    
    return None

def find_ffmpeg():
    """
    Find ffmpeg executable in the system or in the project directory.
    
    Returns:
        str: Path to ffmpeg executable or None if not found
    """
    # First check if ffmpeg is in PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    
    # Check in the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    ffmpeg_exe = os.path.join(project_root, "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe):
        return ffmpeg_exe
    
    # Check in the current directory
    current_dir = os.path.abspath(os.path.dirname(__file__))
    ffmpeg_exe = os.path.join(current_dir, "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe):
        return ffmpeg_exe
    
    return None

def download_with_yt_dlp(url, output_filename):
    """
    Download audio from YouTube using yt-dlp.
    
    Args:
        url (str): YouTube URL
        output_filename (str): Output filename
        
    Returns:
        str: Path to the downloaded file or None if failed
    """
    try:
        # Find ffmpeg
        ffmpeg_path = find_ffmpeg()
        if ffmpeg_path:
            print(f"Found ffmpeg at: {ffmpeg_path}")
        else:
            print("Warning: ffmpeg not found. Audio conversion may fail.")
        
        # Full output path (without extension, yt-dlp will add it)
        output_file = output_filename
        
        # Try to import yt_dlp directly first (preferred method)
        try:
            import yt_dlp
            
            print("Using yt-dlp Python module...")
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': f'{output_file}.%(ext)s',
                'quiet': False,
                'no_warnings': False
            }
            
            # Add ffmpeg location if found
            if ffmpeg_path:
                ydl_opts['ffmpeg_location'] = os.path.dirname(ffmpeg_path)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            # Check for the output file with mp3 extension
            expected_output = f"{output_file}.mp3"
            if os.path.exists(expected_output):
                print(f"Successfully downloaded with yt-dlp module to: {expected_output}")
                return expected_output
            else:
                # Try to find any file that starts with the output filename
                dir_path = os.path.dirname(output_file) or '.'
                base_name = os.path.basename(output_file)
                for file in os.listdir(dir_path):
                    if file.startswith(base_name) and file.endswith('.mp3'):
                        full_path = os.path.join(dir_path, file)
                        print(f"Found downloaded file: {full_path}")
                        return full_path
                
                print(f"Could not find downloaded file with base name: {base_name}")
                return None
                
        except ImportError:
            print("yt-dlp Python module not available, trying command line...")
            
            # Check if yt-dlp is installed as a command
            if not shutil.which("yt-dlp"):
                print("yt-dlp command not found. Install with: pip install yt-dlp")
                return None
            
            # Build the yt-dlp command
            cmd = [
                "yt-dlp",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",  # Best quality
                "-o", f"{output_file}.%(ext)s",
                url
            ]
            
            # Add ffmpeg location if found
            if ffmpeg_path:
                cmd.extend(["--ffmpeg-location", os.path.dirname(ffmpeg_path)])
            
            print("Attempting download with yt-dlp command...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                expected_output = f"{output_file}.mp3"
                if os.path.exists(expected_output):
                    print(f"Successfully downloaded with yt-dlp command to: {expected_output}")
                    return expected_output
                else:
                    # Try to find any file that starts with the output filename
                    dir_path = os.path.dirname(output_file) or '.'
                    base_name = os.path.basename(output_file)
                    for file in os.listdir(dir_path):
                        if file.startswith(base_name) and file.endswith('.mp3'):
                            full_path = os.path.join(dir_path, file)
                            print(f"Found downloaded file: {full_path}")
                            return full_path
                    
                    print(f"Could not find downloaded file with base name: {base_name}")
                    return None
            else:
                print(f"yt-dlp command failed: {result.stderr}")
                return None
                
    except Exception as e:
        print(f"Error with yt-dlp: {e}")
        return None

def download_audio(video_id_or_url, output_filename="downloaded_audio"):
    """
    Download audio from a YouTube video.
    
    Args:
        video_id_or_url (str): YouTube video ID or URL
        output_filename (str): Name for the output file (without extension)
        
    Returns:
        str: Path to the downloaded audio file or None if download failed
    """
    # Extract video ID if URL was provided
    video_id = extract_video_id(video_id_or_url)
    if not video_id:
        video_id = video_id_or_url
        
    # Construct YouTube URL
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    print(f"Downloading audio from: {url}")
    
    # Try yt-dlp as the primary method
    print("Downloading with yt-dlp...")
    yt_dlp_result = download_with_yt_dlp(url, output_filename)
    if yt_dlp_result:
        return yt_dlp_result
    
    print("Failed to download audio from YouTube.")
    return None 