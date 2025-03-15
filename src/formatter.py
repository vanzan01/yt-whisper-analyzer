"""
Module for formatting analysis results.
"""

import json
import sys

# ANSI color codes
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BOLD = "\033[1m"
RESET = "\033[0m"

# 8-bit style pixel art for "cryptobanter"
CRYPTO_BANTER = [
    RED + "█▀▀ █▀█ █▄█ █▀█ ▀█▀ █▀█" + WHITE + "   █▀▄ █▀█ █▄ █ ▀█▀ █▀▀ █▀█" + RESET,
    RED + "█   █▀▄  █  █▀▀  █  █ █" + WHITE + "   █▀▄ █▀█ █ ▀█  █  █▀▀ █▀▄" + RESET,
    RED + "▀▀▀ ▀ ▀  ▀  ▀    ▀  ▀▀▀" + WHITE + "   ▀▀  ▀ ▀ ▀  ▀  ▀  ▀▀▀ ▀ ▀" + RESET
]

def format_crypto_banter():
    """Format the crypto banter ASCII art into a string."""
    lines = ["\n"]
    for line in CRYPTO_BANTER:
        lines.append("  " + line)
    lines.append("\n")
    return "\n".join(lines)

def create_box(content, width=70, title=None, style="single", color=None):
    """
    Create a box around text with optional title
    """
    box = {
        "single": {
            "top_left": "┌", "top_right": "┐", "bottom_left": "└", "bottom_right": "┘",
            "horizontal": "─", "vertical": "│", "title_left": "─ ", "title_right": " ─"
        },
        "double": {
            "top_left": "╔", "top_right": "╗", "bottom_left": "╚", "bottom_right": "╝",
            "horizontal": "═", "vertical": "║", "title_left": "═ ", "title_right": " ═"
        },
        "rounded": {
            "top_left": "╭", "top_right": "╮", "bottom_left": "╰", "bottom_right": "╯",
            "horizontal": "─", "vertical": "│", "title_left": "─ ", "title_right": " ─"
        }
    }[style]
    
    # Apply color if specified
    color_code = ""
    if color:
        color_code = eval(color.upper()) if color.upper() in globals() else ""
    
    # Create box top
    result = []
    if title:
        title_text = f"{box['title_left']}{title}{box['title_right']}"
        padding = width - len(title) - len(box['title_left']) - len(box['title_right'])
        result.append(f"{color_code}{box['top_left']}{title_text}{box['horizontal'] * padding}{box['top_right']}{RESET}")
    else:
        result.append(f"{color_code}{box['top_left']}{box['horizontal'] * width}{box['top_right']}{RESET}")
    
    # Add content
    if isinstance(content, str):
        lines = content.split('\n')
    else:
        lines = content
    
    for line in lines:
        # Strip ANSI color codes for width calculation
        stripped_line = strip_ansi_codes(line)
        
        # Ensure line fits in box width
        if len(stripped_line) > width - 2:
            # Wrap text
            wrapped_lines = []
            current_line = ""
            words = line.split()
            
            for word in words:
                stripped_word = strip_ansi_codes(word)
                if len(strip_ansi_codes(current_line) + stripped_word) + 1 <= width - 2:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
                else:
                    if current_line:
                        wrapped_lines.append(current_line)
                    current_line = word
                    
            if current_line:
                wrapped_lines.append(current_line)
                
            if not wrapped_lines:
                # If we couldn't wrap properly, just truncate
                wrapped_lines = [line[:width-2]]
                
            for wrapped in wrapped_lines:
                stripped_wrapped = strip_ansi_codes(wrapped)
                padding = width - 2 - len(stripped_wrapped)
                result.append(f"{color_code}{box['vertical']} {wrapped}{' ' * padding} {box['vertical']}{RESET}")
        else:
            padding = width - 2 - len(stripped_line)
            result.append(f"{color_code}{box['vertical']} {line}{' ' * padding} {box['vertical']}{RESET}")
    
    # Create box bottom
    result.append(f"{color_code}{box['bottom_left']}{box['horizontal'] * width}{box['bottom_right']}{RESET}")
    
    return '\n'.join(result)

def strip_ansi_codes(text):
    """Remove ANSI color codes for accurate width calculation"""
    import re
    ansi_pattern = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_pattern.sub('', text)

def format_results(analysis_results, format_type="text", include_contexts=True):
    """
    Formats the analysis results into a readable output
    """
    # If JSON format is requested, return the JSON string
    if format_type == "json":
        import json
        return json.dumps(analysis_results, indent=2)
    
    results = ""
    
    # Add the header - use format_crypto_banter() to get the red and white logo
    results += format_crypto_banter()
    
    # Create analysis header
    header = create_box(" YOUTUBE TRANSCRIPT ANALYSIS ", width=70, style="double", color="CYAN")
    results += f"{header}\n\n"
    
    # Check if there are any errors
    if 'errors' in analysis_results and analysis_results['errors']:
        error_content = f"{BOLD}ERRORS DURING ANALYSIS:{RESET}\n\n"
        for error in analysis_results['errors']:
            error_content += f"{RED}• {error}{RESET}\n"
        results += create_box(error_content, width=70, title="ERRORS", style="rounded", color="RED")
        results += "\n\n"
    
    # Create the summary section
    has_timestamps = any(
        keyword_data.get('contexts', []) and 
        any(context.get('timestamp') for context in keyword_data.get('contexts', []))
        for keyword_data in analysis_results.get('keywords', {}).values()
    )
    
    summary_content = [
        f"{BOLD}SUMMARY{RESET}",
        "",
        f"Total words in transcript: {BOLD}{CYAN}{analysis_results.get('total_words', 0)}{RESET}",
        f"Total keyword matches: {BOLD}{GREEN}{analysis_results.get('total_matches', 0)}{RESET}",
        ""
    ]
    
    if has_timestamps:
        summary_content.append(f"{YELLOW}Timestamps are available for keyword occurrences{RESET}")
    else:
        summary_content.append(f"{YELLOW}No timestamps available in transcript{RESET}")
    
    results += create_box(summary_content, width=70, title="SUMMARY", style="rounded", color="BLUE")
    results += "\n\n"
    
    # Create the keyword summary table
    if 'keywords' in analysis_results and analysis_results['keywords']:
        keyword_table = [
            f"{BOLD}KEYWORD SUMMARY{RESET}",
            "",
            f"{BOLD}{'Keyword':<20} {'Exact':^7} {'Partial':^8} {'Total':^7} {'Frequency':^10}{RESET}"
        ]
        
        for keyword, data in analysis_results['keywords'].items():
            # Color code based on number of matches
            color = RED
            if data['exact_matches'] > 5:
                color = GREEN
            elif data['exact_matches'] > 0:
                color = YELLOW
                
            keyword_table.append(
                f"{color}{keyword:<20} {data['exact_matches']:^7} {data['partial_matches']:^8} "
                f"{data['total_matches']:^7} {data.get('frequency', 0.0):.2f}%{RESET}"
            )
        
        results += create_box(keyword_table, width=70, title="KEYWORDS", style="rounded", color="BLUE")
        results += "\n\n"
        
        # Detailed keyword analysis
        for keyword, data in analysis_results['keywords'].items():
            # Color based on number of matches
            color = RED
            if data['exact_matches'] > 5:
                color = GREEN
            elif data['exact_matches'] > 0:
                color = YELLOW
                
            keyword_detail = [
                f"{BOLD}KEYWORD: '{keyword}'{RESET}",
                "",
                f"  Exact matches: {BOLD}{color}{data['exact_matches']}{RESET}",
                f"  Partial matches: {data['partial_matches']}",
                f"  Total matches: {BOLD}{data['total_matches']}{RESET}",
                f"  Frequency: {BOLD}{data.get('frequency', 0.0):.2f}%{RESET} of total words",
                ""
            ]
            
            # Add sample contexts if available
            if 'contexts' in data and data['contexts'] and include_contexts:
                keyword_detail.append(f"  {BOLD}ALL CONTEXT OCCURRENCES:{RESET}")
                keyword_detail.append("")
                
                for i, context in enumerate(data['contexts'], 1):
                    if 'timestamp' in context and context['timestamp']:
                        start_time = context['timestamp']['start']
                        end_time = context['timestamp']['end']
                        
                        # Format timestamp as HH:MM:SS
                        start_formatted = start_time if isinstance(start_time, str) else format_timestamp(start_time)
                        end_formatted = end_time if isinstance(end_time, str) else format_timestamp(end_time)
                        
                        timestamp_str = f"{CYAN}[{start_formatted} - {end_formatted}]{RESET}"
                        keyword_detail.append(f"  {i}. {timestamp_str}")
                    else:
                        keyword_detail.append(f"  {i}. {YELLOW}[No timestamp available]{RESET}")
                    
                    # Format the context text to highlight the keyword
                    context_text = context['text']
                    # Highlight the keyword in the context
                    highlighted_text = highlight_keyword(context_text, keyword)
                    
                    # Split the context into multiple lines for readability
                    context_lines = split_text(highlighted_text, width=60)
                    for line in context_lines:
                        keyword_detail.append(f"  {line}")
                    
                    keyword_detail.append("")
            
            results += create_box(keyword_detail, width=70, title=keyword, style="single", color=color)
            results += "\n\n"
    
    # Add the footer (only once)
    results += f"{GREEN}{BOLD}Analysis complete!{RESET}\n"
    
    return results

def format_timestamp(seconds):
    """Format seconds into HH:MM:SS format"""
    # Convert seconds to float to ensure compatibility
    try:
        seconds_float = float(seconds)
        hours = int(seconds_float / 3600)
        minutes = int((seconds_float % 3600) / 60)
        secs = int(seconds_float % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    except (ValueError, TypeError):
        # If seconds cannot be converted to float, return a default format
        return "00:00:00"

def highlight_keyword(text, keyword):
    """Highlight the keyword in the text with ANSI colors"""
    # Case-insensitive replacement
    import re
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(f"{BOLD}{GREEN}\\g<0>{RESET}", text)

def split_text(text, width=60):
    """Split text into multiple lines for better readability"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines

def save_results(formatted_results, output_file):
    """
    Save formatted results to a file.
    
    Args:
        formatted_results (str): Formatted results
        output_file (str): Path to output file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_results)
        print(f"Results saved to: {output_file}")
        return True
    except Exception as e:
        print(f"Error saving results: {e}")
        return False 