"""
Module for analyzing transcripts for keyword occurrences.
"""

import re
import json
from collections import Counter

def count_keywords(transcript, keywords):
    """
    Count occurrences of keywords in transcript.
    
    Args:
        transcript (str or dict): Transcript text or dictionary with text and timestamps
        keywords (list): List of keywords to count
        
    Returns:
        dict: Dictionary with keyword counts and statistics
    """
    # Handle potential dictionary format with timestamps
    has_timestamps = False
    timestamp_segments = []
    
    if isinstance(transcript, dict) and 'text' in transcript:
        has_timestamps = 'segments' in transcript and transcript['segments']
        if has_timestamps:
            timestamp_segments = transcript['segments']
            transcript_text = transcript['text']
        else:
            transcript_text = transcript['text']
    else:
        transcript_text = transcript
    
    if not transcript_text or not keywords:
        return {"error": "Empty transcript or no keywords provided"}
    
    # Convert transcript to lowercase for case-insensitive matching
    transcript_lower = transcript_text.lower()
    
    results = {}
    total_words = len(transcript_lower.split())
    results["total_words"] = total_words
    results["keywords"] = {}
    
    # Count occurrences of each keyword
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        # Count exact matches (word boundaries)
        pattern = r'\b' + re.escape(keyword_lower) + r'\b'
        exact_matches = len(re.findall(pattern, transcript_lower))
        
        # Count partial matches (keyword appears within other words)
        partial_matches = transcript_lower.count(keyword_lower) - exact_matches
        
        # Calculate frequency percentage (exact matches per 100 words)
        frequency_percentage = (exact_matches / total_words) * 100 if total_words > 0 else 0
        
        # Store keyword analysis data
        results["keywords"][keyword] = {
            "exact_matches": exact_matches,
            "partial_matches": partial_matches,
            "total_matches": exact_matches + partial_matches,
            "frequency": frequency_percentage
        }
        
        # Get context for each match (all instances with timestamps)
        contexts = []
        if exact_matches > 0:
            for match in re.finditer(pattern, transcript_lower):
                # Use more context (100 characters before and after instead of 50)
                start = max(0, match.start() - 100)
                end = min(len(transcript_lower), match.end() + 100)
                context = transcript_text[start:end]
                
                # Highlight the keyword in context
                match_text = transcript_text[match.start():match.end()]
                highlighted = context.replace(match_text, f"**{match_text}**")
                
                # Context data with basic info
                context_data = {
                    "text": highlighted,
                    "position": match.start()
                }
                
                # If we have timestamps, find the relevant segment
                if has_timestamps:
                    match_timestamp = find_timestamp_for_position(match.start(), timestamp_segments, transcript_text)
                    if match_timestamp:
                        context_data["timestamp"] = match_timestamp
                
                contexts.append(context_data)
        
        results["keywords"][keyword]["contexts"] = contexts
    
    # Calculate total matches across all keywords
    total_matches = sum(item["exact_matches"] for item in results["keywords"].values())
    results["total_matches"] = total_matches
    
    # Sort keywords by number of matches (descending)
    results["sorted_keywords"] = sorted(
        results["keywords"].items(),
        key=lambda x: x[1]["exact_matches"],
        reverse=True
    )
    
    # Include whether timestamps were available
    results["has_timestamps"] = has_timestamps
    
    return results

def find_timestamp_for_position(position, segments, transcript_text):
    """
    Find the timestamp information for a specific position in the transcript.
    
    Args:
        position (int): Character position in the transcript
        segments (list): List of transcript segments with timestamps
        transcript_text (str): Full transcript text
        
    Returns:
        dict: Dictionary with start and end timestamps, or None if not found
    """
    if not segments:
        return None
    
    # First, try to find a direct match in any segment
    for segment in segments:
        if not isinstance(segment, dict):
            # Skip non-dictionary segments
            continue
            
        # Check if segment has the necessary attributes
        if 'text' not in segment or 'start' not in segment or 'end' not in segment:
            continue
            
        segment_text = segment.get('text', '')
        
        # Skip empty segments
        if not segment_text:
            continue
            
        # Try to find this segment in the transcript
        segment_pos = transcript_text.find(segment_text)
        if segment_pos != -1:
            # Check if our position is within this segment
            if position >= segment_pos and position <= segment_pos + len(segment_text):
                return {
                    "start": format_timestamp(segment.get('start', 0)),
                    "end": format_timestamp(segment.get('end', 0)),
                    "text": segment_text,
                    "exact_match": True
                }
    
    # If no direct match, look for overlapping segments
    for segment in segments:
        if not isinstance(segment, dict):
            continue
            
        if 'text' not in segment or 'start' not in segment or 'end' not in segment:
            continue
            
        segment_text = segment.get('text', '')
        
        # Try to find our position in any segment using fuzzy matching
        for i in range(max(0, position-100), min(len(transcript_text), position+100)):
            if i <= len(transcript_text) - len(segment_text):
                window = transcript_text[i:i+len(segment_text)]
                # Use a similarity measure to check if this window is close to our segment
                if similarity(window.lower(), segment_text.lower()) > 0.8:
                    if i <= position <= i + len(segment_text):
                        return {
                            "start": format_timestamp(segment.get('start', 0)),
                            "end": format_timestamp(segment.get('end', 0)),
                            "text": segment_text,
                            "fuzzy_match": True
                        }
    
    # If still no match, use the closest segment by position
    if segments:
        # Get total transcript length
        total_length = len(transcript_text)
        
        # Calculate position ratio (how far into the transcript we are)
        position_ratio = position / total_length
        
        # Get total duration from last segment
        if isinstance(segments[-1], dict) and 'end' in segments[-1]:
            total_duration = segments[-1].get('end', 0)
            
            # Estimate time based on position ratio
            estimated_time = position_ratio * total_duration
            
            # Find segment closest to this estimated time
            closest_segment = None
            min_distance = float('inf')
            
            for segment in segments:
                if not isinstance(segment, dict):
                    continue
                    
                if 'start' not in segment or 'end' not in segment:
                    continue
                    
                # Calculate middle time point of this segment
                segment_mid = (segment.get('start', 0) + segment.get('end', 0)) / 2
                
                # Calculate distance to our estimated time
                distance = abs(estimated_time - segment_mid)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_segment = segment
            
            if closest_segment:
                return {
                    "start": format_timestamp(closest_segment.get('start', 0)),
                    "end": format_timestamp(closest_segment.get('end', 0)),
                    "text": closest_segment.get('text', ''),
                    "estimated": True
                }
    
    # If all else fails, estimate timestamp based on position in text
    if segments and isinstance(segments[-1], dict) and 'end' in segments[-1]:
        total_duration = segments[-1].get('end', 0)
        estimated_time = (position / len(transcript_text)) * total_duration
        
        return {
            "start": format_timestamp(estimated_time),
            "end": format_timestamp(estimated_time + 5),  # Add 5 seconds as an estimate
            "text": "Estimated timestamp",
            "rough_estimate": True
        }
    
    return None

def similarity(text1, text2):
    """
    Calculate a simple similarity score between two strings.
    
    Args:
        text1 (str): First string
        text2 (str): Second string
        
    Returns:
        float: Similarity score between 0 and 1
    """
    # Use a simple similarity metric based on character overlap
    if not text1 or not text2:
        return 0
        
    # Get the shorter and longer text
    shorter = text1 if len(text1) <= len(text2) else text2
    longer = text2 if len(text1) <= len(text2) else text1
    
    # Count matching characters
    matches = sum(1 for c in shorter if c in longer)
    
    # Return similarity score
    return matches / len(shorter)

def format_timestamp(seconds):
    """
    Format seconds as HH:MM:SS.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted time string
    """
    if not isinstance(seconds, (int, float)):
        return "00:00:00"
        
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def find_related_terms(transcript, keywords, threshold=0.7):
    """
    Find terms in the transcript that might be related to the provided keywords.
    
    Args:
        transcript (str or dict): Transcript text or dictionary with text and timestamps
        keywords (list): List of primary keywords
        threshold (float): Similarity threshold for considering words related
        
    Returns:
        dict: Dictionary with related terms for each keyword
    """
    # Handle potential dictionary format with timestamps
    if isinstance(transcript, dict) and 'text' in transcript:
        transcript_text = transcript['text']
    else:
        transcript_text = transcript
    
    if not transcript_text or not keywords:
        return {}
    
    # Extract all words from transcript
    words = re.findall(r'\b[a-z]{3,}\b', transcript_text.lower())
    
    # Filter out common stop words
    stop_words = {'the', 'and', 'that', 'for', 'you', 'this', 'with', 'have', 'from', 'are', 'was', 'were'}
    filtered_words = [word for word in words if word not in stop_words]
    
    # Count word frequencies
    word_counts = Counter(filtered_words)
    
    # Find related terms for each keyword
    related_terms = {}
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        related = {}
        
        # First, find terms that contain the keyword or are contained by it
        for word, count in word_counts.most_common(100):
            # Skip exact matches
            if word == keyword_lower:
                continue
                
            # Check if the word contains the keyword or vice versa
            if keyword_lower in word or word in keyword_lower:
                related[word] = count
        
        # Look for words that frequently appear near the keyword
        keyword_pattern = re.compile(r'\b' + re.escape(keyword_lower) + r'\b')
        keyword_matches = list(keyword_pattern.finditer(transcript_text.lower()))
        
        if keyword_matches:
            # Extract context around each keyword occurrence
            for match in keyword_matches:
                start_pos = max(0, match.start() - 150)
                end_pos = min(len(transcript_text), match.end() + 150)
                context = transcript_text[start_pos:end_pos].lower()
                
                # Find words in this context
                context_words = re.findall(r'\b[a-z]{3,}\b', context)
                for word in context_words:
                    if word != keyword_lower and word not in stop_words:
                        related[word] = related.get(word, 0) + 1
        
        # Sort related terms by count and take the top 10
        related_terms[keyword] = dict(sorted(related.items(), key=lambda x: x[1], reverse=True)[:10])
    
    return related_terms 