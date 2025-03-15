#!/usr/bin/env python
"""
Script to view saved transcript analysis results.

This script loads saved YouTube transcript analysis data (in JSON format) and 
displays it in the same formatted output as seen at the end of running the
run_analysis.py script. This allows users to access previous analysis results
without having to re-run the analysis.

The displayed output includes:
- The Crypto Banter logo
- A summary of total words and keyword matches
- A detailed breakdown of each keyword with exact and partial matches
- All occurrences of each keyword with their timestamps and surrounding context

Usage:
  python view_analysis.py [analysis_file.json]
  python view_analysis.py --interactive

Example:
  python view_analysis.py output/analysis_dQw4w9WgXcQ_20230415_123456_raw.json
"""

import os
import sys
import json
import argparse
import glob
import datetime
from src.formatter import format_results

# Try to load required libraries
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import print as rprint
    rich_available = True
except ImportError:
    rich_available = False

try:
    import questionary
    from questionary import Style
    questionary_available = True
except ImportError:
    questionary_available = False

# Custom questionary style
custom_style = Style([
    ('qmark', 'fg:red bold'),
    ('question', 'fg:white bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:red bold'),
    ('selected', 'fg:green bold'),
    ('highlighted', 'fg:red bold'),
]) if questionary_available else None

# Set up Rich console
console = Console() if rich_available else None

def find_analysis_files(output_dir="output"):
    """
    Find all analysis result files in the specified directory.
    
    Args:
        output_dir (str): Directory to search for analysis files
        
    Returns:
        list: List of analysis file paths
    """
    # Check if directory exists
    if not os.path.exists(output_dir):
        return []
    
    # Find all raw analysis JSON files
    pattern = os.path.join(output_dir, "analysis_*_raw.json")
    files = glob.glob(pattern)
    
    # Sort files by modification time (newest first)
    files.sort(key=os.path.getmtime, reverse=True)
    
    return files

def extract_keywords_from_file(file_path):
    """
    Extract keywords from an analysis file.
    
    Args:
        file_path (str): Path to analysis file
        
    Returns:
        str: Comma-separated list of keywords
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'keywords' in data:
            keywords = list(data['keywords'].keys())
            return ", ".join(keywords)
        return "No keywords found"
    except Exception:
        return "Error reading keywords"

def get_video_info_from_filename(filename):
    """
    Extract video ID and timestamp from filename.
    
    Args:
        filename (str): Path to analysis file
        
    Returns:
        tuple: (video_id, timestamp)
    """
    basename = os.path.basename(filename)
    # Format is analysis_VIDEO_ID_TIMESTAMP_raw.json
    parts = basename.split('_')
    
    if len(parts) >= 4:
        video_id = parts[1]
        timestamp = '_'.join(parts[2:-1])  # Join all parts between video_id and _raw.json
        return video_id, timestamp
    
    return "unknown", "unknown"

def interactive_mode():
    """
    Run in interactive mode, allowing user to select from available analysis files.
    
    Returns:
        str: Selected file path or None if cancelled
    """
    if not rich_available or not questionary_available:
        print("Interactive mode requires rich and questionary libraries.")
        print("Please install them with: pip install rich questionary")
        return None
    
    # Display header
    if rich_available:
        from src.cryptobanter import print_crypto_banter
        print_crypto_banter()
        console.print(Panel("[bold red]YouTube Whisper Analyzer[/bold red] - [white]Analysis Viewer[/white]", 
                         border_style="red", expand=False))
    
    # Find analysis files
    output_dir = questionary.text(
        "Enter output directory to search (press Enter for default 'output'):",
        default="output",
        style=custom_style
    ).ask()
    
    files = find_analysis_files(output_dir)
    
    if not files:
        console.print(f"[bold red]No analysis files found in {output_dir}[/bold red]")
        return None
    
    # Create formatted choices for each file
    choices = []
    for file in files:
        video_id, timestamp = get_video_info_from_filename(file)
        # Try to get file size and formatted date
        size_mb = os.path.getsize(file) / (1024 * 1024)
        mod_time = os.path.getmtime(file)
        mod_date = datetime.datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract keywords from the file
        keywords = extract_keywords_from_file(file)
        
        # Format the choice label
        label = f"{video_id} ({mod_date}) - {size_mb:.2f}MB - Keywords: {keywords}"
        choices.append({"name": label, "value": file})
    
    # Add option to specify a different file
    choices.append({"name": "[Specify a different file path]", "value": "custom"})
    
    # Let user select a file
    if rich_available:
        console.print("[yellow]Tip:[/yellow] Use arrow keys to navigate, Enter to select")
        console.print("[yellow]Tip:[/yellow] Looking for specific keywords? They're shown in each option")
    
    selected = questionary.select(
        "Select an analysis file to view:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if selected == "custom":
        custom_file = questionary.text(
            "Enter path to analysis file:",
            style=custom_style
        ).ask()
        
        if not custom_file or not os.path.exists(custom_file):
            console.print(f"[bold red]File not found: {custom_file}[/bold red]")
            return None
        
        return custom_file
    
    return selected

def main():
    """Main entry point for the analysis viewer."""
    # Check for interactive mode flag
    if '--interactive' in sys.argv or '-i' in sys.argv:
        file_path = interactive_mode()
        if file_path is None:
            return 1
    else:
        # Regular command line mode
        parser = argparse.ArgumentParser(
            description="View saved transcript analysis results in a formatted display",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python view_analysis.py output/analysis_videoID_20230415_123456_raw.json
  python view_analysis.py --interactive
            """
        )
        parser.add_argument("file", nargs="?", help="Path to the saved analysis results file (JSON format)")
        parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
        args = parser.parse_args()
        
        # If interactive flag is set, enter interactive mode
        if args.interactive:
            file_path = interactive_mode()
            if file_path is None:
                return 1
        elif args.file:
            file_path = args.file
        else:
            parser.print_help()
            return 1
    
    # Check if file exists
    if not os.path.exists(file_path):
        if rich_available:
            console.print(f"[bold red]Error: File not found: {file_path}[/bold red]")
        else:
            print(f"Error: File not found: {file_path}")
        return 1
    
    # Load the analysis results
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            analysis_results = json.load(f)
        
        # Handle timestamps which might have been serialized as strings
        if 'keywords' in analysis_results:
            for keyword, data in analysis_results['keywords'].items():
                if 'contexts' in data:
                    for context in data['contexts']:
                        if 'timestamp' in context:
                            # Ensure timestamp is in the expected format
                            if isinstance(context['timestamp'], str):
                                try:
                                    # If it's a string, try to parse it back to a dict
                                    context['timestamp'] = json.loads(context['timestamp'])
                                except:
                                    # If parsing fails, keep it as is
                                    pass
                                    
        # Format and display the results
        formatted_results = format_results(analysis_results, "text")
        print("\n" + formatted_results)
        
        return 0
    except json.JSONDecodeError:
        if rich_available:
            console.print(f"[bold red]Error: File is not valid JSON: {file_path}[/bold red]")
        else:
            print(f"Error: File is not valid JSON: {file_path}")
        return 1
    except Exception as e:
        if rich_available:
            console.print(f"[bold red]Error loading or displaying results: {e}[/bold red]")
        else:
            print(f"Error loading or displaying results: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 