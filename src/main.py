"""
Main module for YouTube Whisper Analyzer.
"""

import os
import argparse
import time
import datetime
from .downloader import download_audio, extract_video_id
from .transcriber import transcribe_audio, save_transcript, load_api_key
from .analyzer import count_keywords, find_related_terms
from .formatter import format_results, save_results

# Try to load dotenv for environment variables
try:
    from dotenv import load_dotenv
    # Load from .env file in project root
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    dotenv_available = True
except ImportError:
    dotenv_available = False

def get_default_model():
    """Get default Whisper model from .env or use hardcoded default"""
    return os.environ.get("WHISPER_MODEL", "whisper-large-v3")

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Analyze keyword frequency in YouTube video transcripts")
    
    # Add URL/ID arguments (mutually exclusive)
    url_group = parser.add_mutually_exclusive_group(required=True)
    url_group.add_argument("--url", help="YouTube video URL")
    url_group.add_argument("--video_id", help="YouTube video ID")
    
    # Add other arguments
    parser.add_argument("--keywords", required=True, help="Comma-separated list of keywords to analyze")
    parser.add_argument("--output", default="text", choices=["text", "json"], help="Output format (text, json)")
    parser.add_argument("--model", default=get_default_model(), help="Whisper model to use")
    parser.add_argument("--api_key", help="Groq API key (alternatively, set GROQ_API_KEY in .env file or environment variable)")
    parser.add_argument("--save_transcript", action="store_true", help="Save transcript to file")
    parser.add_argument("--save_results", action="store_true", help="Save analysis results to file")
    parser.add_argument("--output_dir", default="output", help="Directory for output files")
    
    args = parser.parse_args()
    
    # Create timestamp for file naming
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Process URL/video_id
    video_id = args.video_id if args.video_id else extract_video_id(args.url)
    if not video_id:
        print("Error: Invalid YouTube URL or video ID")
        return 1
    
    # Process keywords
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if not keywords:
        print("Error: No valid keywords provided")
        return 1
    
    # Create output directory if needed
    if (args.save_transcript or args.save_results) and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Step 1: Download audio
    print(f"\n=== STEP 1: DOWNLOADING YOUTUBE AUDIO ===")
    output_filename = f"yt_{video_id}"
    audio_file = download_audio(video_id, output_filename)
    if not audio_file:
        print("Error: Failed to download audio")
        return 1
    
    # Step 2: Transcribe audio
    print(f"\n=== STEP 2: TRANSCRIBING AUDIO ===")
    transcript = transcribe_audio(audio_file, args.api_key, args.model)
    if not transcript:
        print("Error: Failed to transcribe audio")
        # Clean up audio file
        if os.path.exists(audio_file):
            os.remove(audio_file)
        return 1
    
    # Save transcript if requested
    if args.save_transcript:
        transcript_file = os.path.join(args.output_dir, f"transcript_{video_id}_{timestamp}.txt")
        save_transcript(transcript, transcript_file)
    
    # Step 3: Analyze transcript
    print(f"\n=== STEP 3: ANALYZING TRANSCRIPT ===")
    analysis_results = count_keywords(transcript, keywords)
    
    # Find related terms
    related_terms = find_related_terms(transcript, keywords)
    if related_terms:
        analysis_results["related_terms"] = related_terms
    
    # Step 4: Format and output results
    print(f"\n=== STEP 4: FORMATTING RESULTS ===")
    formatted_results = format_results(analysis_results, args.output)
    
    # Print results
    print("\n" + formatted_results)
    
    # Save results if requested
    if args.save_results:
        results_file = os.path.join(args.output_dir, f"analysis_{video_id}_{timestamp}.{args.output}")
        save_results(formatted_results, results_file)
    
    # Clean up audio file
    if os.path.exists(audio_file):
        os.remove(audio_file)
        print(f"\nCleaned up temporary audio file")
    
    print(f"\nAnalysis complete!")
    return 0

if __name__ == "__main__":
    exit(main()) 