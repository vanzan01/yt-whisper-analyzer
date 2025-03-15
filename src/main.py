"""
Main module for YouTube Whisper Analyzer.
"""

import os
import argparse
import time
import datetime
import sys
import json
from .downloader import download_audio, extract_video_id
from .transcriber import transcribe_audio, save_transcript, load_api_key, load_transcript, find_existing_transcript
from .analyzer import count_keywords, find_related_terms
from .formatter import format_results, save_results
from .cryptobanter import print_crypto_banter

# Try to load required libraries
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import print as rprint
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
    rich_available = True
except ImportError:
    rich_available = False

try:
    import questionary
    from questionary import Style
    questionary_available = True
except ImportError:
    questionary_available = False

# Try to load dotenv for environment variables
try:
    from dotenv import load_dotenv
    # Load from .env file in project root
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print("Loaded environment from .env file")
    dotenv_available = True
except ImportError:
    dotenv_available = False

# Set up Rich console
console = Console() if rich_available else None

# Custom questionary style
custom_style = Style([
    ('qmark', 'fg:red bold'),
    ('question', 'fg:white bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:red bold'),
    ('selected', 'fg:green bold'),
    ('highlighted', 'fg:red bold'),
]) if questionary_available else None

def get_default_model():
    """Get default Whisper model from .env or use hardcoded default"""
    return os.environ.get("WHISPER_MODEL", "whisper-large-v3")

def interactive_mode():
    """Run in interactive mode, prompting user for options"""
    if not rich_available or not questionary_available:
        print("Interactive mode requires rich and questionary libraries.")
        print("Please install them with: pip install rich questionary")
        return None
    
    # Display welcome banner
    print_crypto_banter()
    
    console.print(Panel("[bold red]YouTube Whisper Analyzer[/bold red] - [white]Interactive Mode[/white]", 
                       border_style="red", expand=False))
    
    # Get YouTube URL or video ID
    url_or_id = questionary.select(
        "How would you like to specify the video?",
        choices=["YouTube URL", "Video ID"],
        style=custom_style
    ).ask()
    
    if url_or_id == "YouTube URL":
        url = questionary.text("Enter YouTube URL:", style=custom_style).ask()
        if not url:
            console.print("[bold red]Error:[/bold red] No URL provided")
            return None
        video_id = extract_video_id(url)
        if not video_id:
            console.print("[bold red]Error:[/bold red] Invalid YouTube URL")
            return None
    else:
        video_id = questionary.text("Enter YouTube video ID:", style=custom_style).ask()
        if not video_id:
            console.print("[bold red]Error:[/bold red] No video ID provided")
            return None
        url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Get keywords
    keywords_str = questionary.text(
        "Enter keywords to analyze (comma-separated):",
        style=custom_style
    ).ask()
    
    if not keywords_str:
        console.print("[bold red]Error:[/bold red] No keywords provided")
        return None
    
    # Ask about transcript options
    transcript_option = questionary.select(
        "Transcript options:",
        choices=[
            "Download and transcribe new",
            "Check for existing transcript first",
            "Specify local transcript file"
        ],
        style=custom_style
    ).ask()
    
    transcript_file = None
    use_existing = False
    
    if transcript_option == "Specify local transcript file":
        transcript_file = questionary.text(
            "Enter path to transcript file:",
            style=custom_style
        ).ask()
        if not os.path.exists(transcript_file):
            console.print(f"[bold red]Error:[/bold red] File not found: {transcript_file}")
            return None
    elif transcript_option == "Check for existing transcript first":
        use_existing = True
    
    # Ask about saving options
    save_options = questionary.checkbox(
        "Select save options:",
        choices=[
            "Save transcript",
            {"name": "Save analysis results", "checked": True}
        ],
        style=custom_style
    ).ask()
    
    save_transcript_opt = "Save transcript" in save_options
    save_results_opt = "Save analysis results" in save_options
    
    # Ask about output format
    output_format = questionary.select(
        "Select output format for saved results:",
        choices=["text", "json"],
        default="text",
        style=custom_style
    ).ask()
    
    # Output directory
    output_dir = questionary.text(
        "Enter output directory (press Enter for default 'output'):",
        default="output",
        style=custom_style
    ).ask()
    
    # API key
    api_key = None
    if 'GROQ_API_KEY' not in os.environ:
        api_key = questionary.password(
            "Enter Groq API key (leave empty to skip):",
            style=custom_style
        ).ask()
    
    # Show model information panel
    if rich_available:
        console.print(Panel(
            "[bold white]Available Whisper Models:[/bold white]\n\n"
            "[bold green]whisper-large-v3[/bold green]: Best accuracy, multilingual support, most detailed\n"
            "[bold yellow]whisper-large-v3-turbo[/bold yellow]: Good balance of speed and accuracy\n"
            "[bold blue]distil-whisper-large-v3-en[/bold blue]: Fastest option, English-only",
            title="Model Information",
            border_style="yellow",
            expand=False
        ))
    
    # Model selection
    default_model = get_default_model()
    model = questionary.select(
        "Select Whisper model:",
        choices=[
            "whisper-large-v3",
            "whisper-large-v3-turbo",
            "distil-whisper-large-v3-en"
        ],
        default=default_model if default_model in [
            "whisper-large-v3",
            "whisper-large-v3-turbo",
            "distil-whisper-large-v3-en"
        ] else "whisper-large-v3",
        style=custom_style
    ).ask()
    
    # Create command line args
    args = argparse.Namespace(
        url=url,
        video_id=video_id if url_or_id == "Video ID" else None,
        keywords=keywords_str,
        output=output_format,
        model=model,
        api_key=api_key,
        save_transcript=save_transcript_opt,
        save_results=save_results_opt,
        output_dir=output_dir,
        transcript_file=transcript_file,
        use_existing_transcript=use_existing
    )
    
    return args

def main():
    """Main entry point for the application."""
    # Check if running in interactive mode
    if '--interactive' in sys.argv or '-i' in sys.argv:
        args = interactive_mode()
        if args is None:
            return 1
        # Remove interactive flag for arg parsing
        if '--interactive' in sys.argv:
            sys.argv.remove('--interactive')
        if '-i' in sys.argv:
            sys.argv.remove('-i')
    else:
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
        parser.add_argument("--transcript_file", help="Path to local transcript file to use instead of downloading and transcribing")
        parser.add_argument("--use_existing_transcript", action="store_true", help="Look for existing transcript in output directory before downloading and transcribing")
        parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
        
        args = parser.parse_args()
    
    # Make terminal look fancier with cryptobanter logo
    if rich_available:
        print_crypto_banter()
    
    # Create timestamp for file naming
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Process URL/video_id
    video_id = args.video_id if args.video_id else extract_video_id(args.url)
    if not video_id:
        if rich_available:
            console.print("[bold red]Error:[/bold red] Invalid YouTube URL or video ID")
        else:
            print("Error: Invalid YouTube URL or video ID")
        return 1
    
    # Process keywords
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if not keywords:
        if rich_available:
            console.print("[bold red]Error:[/bold red] No valid keywords provided")
        else:
            print("Error: No valid keywords provided")
        return 1
    
    # Create output directory if needed
    if (args.save_transcript or args.save_results) and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Initialize variables
    transcript = None
    audio_file = None
    
    # Check for user-specified transcript file
    if args.transcript_file:
        if rich_available:
            console.print("\n[bold white on red]LOADING USER-SPECIFIED TRANSCRIPT[/bold white on red]")
        else:
            print(f"\n=== LOADING USER-SPECIFIED TRANSCRIPT ===")
        transcript = load_transcript(args.transcript_file)
        if not transcript:
            if rich_available:
                console.print(f"[bold red]Error:[/bold red] Failed to load transcript from {args.transcript_file}")
            else:
                print(f"Error: Failed to load transcript from {args.transcript_file}")
            return 1
    
    # Check for existing transcript if enabled
    elif args.use_existing_transcript:
        if rich_available:
            console.print("\n[bold white on red]CHECKING FOR EXISTING TRANSCRIPT[/bold white on red]")
        else:
            print(f"\n=== CHECKING FOR EXISTING TRANSCRIPT ===")
        existing_transcript_path = find_existing_transcript(video_id, args.output_dir)
        if existing_transcript_path:
            if rich_available:
                console.print(f"Found existing transcript: [green]{existing_transcript_path}[/green]")
            else:
                print(f"Found existing transcript: {existing_transcript_path}")
            transcript = load_transcript(existing_transcript_path)
            if transcript:
                if rich_available:
                    console.print("[green]Successfully loaded existing transcript[/green]")
                else:
                    print("Successfully loaded existing transcript")
            else:
                if rich_available:
                    console.print("[yellow]Failed to load existing transcript, will download and transcribe instead[/yellow]")
                else:
                    print("Failed to load existing transcript, will download and transcribe instead")
    
    # Download and transcribe if needed
    if transcript is None:
        # Step 1: Download audio
        if rich_available:
            console.print("\n[bold white on red]STEP 1: DOWNLOADING YOUTUBE AUDIO[/bold white on red]")
        else:
            print(f"\n=== STEP 1: DOWNLOADING YOUTUBE AUDIO ===")
        output_filename = f"yt_{video_id}"
        audio_file = download_audio(video_id, output_filename)
        if not audio_file:
            if rich_available:
                console.print("[bold red]Error:[/bold red] Failed to download audio")
            else:
                print("Error: Failed to download audio")
            return 1
        
        # Step 2: Transcribe audio
        if rich_available:
            console.print("\n[bold white on red]STEP 2: TRANSCRIBING AUDIO[/bold white on red]")
        else:
            print(f"\n=== STEP 2: TRANSCRIBING AUDIO ===")
        transcript = transcribe_audio(audio_file, args.api_key, args.model)
        if not transcript:
            if rich_available:
                console.print("[bold red]Error:[/bold red] Failed to transcribe audio")
            else:
                print("Error: Failed to transcribe audio")
            # Clean up audio file
            if os.path.exists(audio_file):
                os.remove(audio_file)
            return 1
        
        # Save transcript if requested or if use_existing_transcript is enabled
        # (so it will be available for future runs)
        if args.save_transcript or args.use_existing_transcript:
            transcript_file = os.path.join(args.output_dir, f"transcript_{video_id}_{timestamp}.txt")
            save_transcript(transcript, transcript_file)
    else:
        if rich_available:
            console.print("\n[bold white on red]USING EXISTING TRANSCRIPT[/bold white on red]")
            console.print("[green]Skipped downloading and transcribing[/green]")
        else:
            print(f"\n=== USING EXISTING TRANSCRIPT ===")
            print(f"Skipped downloading and transcribing")
    
    # Step 3: Analyze transcript
    if rich_available:
        console.print("\n[bold white on red]STEP 3: ANALYZING TRANSCRIPT[/bold white on red]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold white]Analyzing keywords..."),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[white]Analyzing...", total=1)
            analysis_results = count_keywords(transcript, keywords)
            progress.update(task, advance=0.5)
            
            # Find related terms
            related_terms = find_related_terms(transcript, keywords)
            if related_terms:
                analysis_results["related_terms"] = related_terms
            progress.update(task, advance=0.5)
    else:
        print(f"\n=== STEP 3: ANALYZING TRANSCRIPT ===")
        analysis_results = count_keywords(transcript, keywords)
        
        # Find related terms
        related_terms = find_related_terms(transcript, keywords)
        if related_terms:
            analysis_results["related_terms"] = related_terms
    
    # Step 4: Format and output results
    if rich_available:
        console.print("\n[bold white on red]STEP 4: FORMATTING RESULTS[/bold white on red]")
    else:
        print(f"\n=== STEP 4: FORMATTING RESULTS ===")
    
    # Always format results as text for display
    formatted_results_display = format_results(analysis_results, "text")
    
    # Format results in requested format for saving
    if args.output != "text":
        formatted_results_save = format_results(analysis_results, args.output)
    else:
        formatted_results_save = formatted_results_display
    
    # Print results
    print("\n" + formatted_results_display)
    
    # Save results if requested
    if args.save_results:
        results_file = os.path.join(args.output_dir, f"analysis_{video_id}_{timestamp}.{args.output}")
        save_results(formatted_results_save, results_file)
        
        # Also save raw analysis results in JSON format for later viewing
        raw_results_file = os.path.join(args.output_dir, f"analysis_{video_id}_{timestamp}_raw.json")
        try:
            # Create a serializable copy of the results
            serializable_results = {}
            
            # Copy basic data
            for key in ['total_words', 'total_matches', 'has_timestamps']:
                if key in analysis_results:
                    serializable_results[key] = analysis_results[key]
                    
            # Handle keywords and contexts
            if 'keywords' in analysis_results:
                serializable_results['keywords'] = {}
                for keyword, data in analysis_results['keywords'].items():
                    serializable_results['keywords'][keyword] = {
                        'exact_matches': data.get('exact_matches', 0),
                        'partial_matches': data.get('partial_matches', 0),
                        'total_matches': data.get('total_matches', 0),
                        'frequency': data.get('frequency', 0.0)
                    }
                    
                    # Handle contexts
                    if 'contexts' in data:
                        serializable_results['keywords'][keyword]['contexts'] = []
                        for ctx in data['contexts']:
                            context_copy = {
                                'text': ctx.get('text', ''),
                                'position': ctx.get('position', 0)
                            }
                            
                            # Handle timestamp objects
                            if 'timestamp' in ctx:
                                context_copy['timestamp'] = {
                                    'start': ctx['timestamp'].get('start', '00:00:00'),
                                    'end': ctx['timestamp'].get('end', '00:00:00')
                                }
                                
                            serializable_results['keywords'][keyword]['contexts'].append(context_copy)
            
            # Save serialized data
            with open(raw_results_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2)
            
            if rich_available:
                console.print(f"Results saved to: [green]{results_file}[/green]")
                console.print(f"Raw analysis data saved to: [green]{raw_results_file}[/green]")
                console.print(f"To view formatted results later, run: [yellow]python view_analysis.py {raw_results_file}[/yellow]")
            else:
                print(f"Results saved to: {results_file}")
                print(f"Raw analysis data saved to: {raw_results_file}")
                print(f"To view formatted results later, run: python view_analysis.py {raw_results_file}")
        except Exception as e:
            if rich_available:
                console.print(f"[bold red]Error saving raw analysis data:[/bold red] {e}")
            else:
                print(f"Error saving raw analysis data: {e}")
    
    # Clean up audio file
    if audio_file and os.path.exists(audio_file):
        os.remove(audio_file)
        if rich_available:
            console.print(f"\n[green]Cleaned up temporary audio file[/green]")
        else:
            print(f"\nCleaned up temporary audio file")
    
    return 0

if __name__ == "__main__":
    exit(main()) 