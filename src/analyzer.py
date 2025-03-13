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
        transcript (str): Transcript text
        keywords (list): List of keywords to count
        
    Returns:
        dict: Dictionary with keyword counts and statistics
    """
    if not transcript or not keywords:
        return {"error": "Empty transcript or no keywords provided"}
    
    # Convert transcript to lowercase for case-insensitive matching
    transcript_lower = transcript.lower()
    
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
        
        # Get context for each match (up to 5 exact matches with surrounding text)
        contexts = []
        if exact_matches > 0:
            for match in re.finditer(pattern, transcript_lower):
                start = max(0, match.start() - 50)
                end = min(len(transcript_lower), match.end() + 50)
                context = transcript[start:end]
                # Highlight the keyword in context
                match_text = transcript[match.start():match.end()]
                highlighted = context.replace(match_text, f"**{match_text}**")
                contexts.append(highlighted)
                if len(contexts) >= 5:  # Limit to 5 contexts
                    break
        
        results["keywords"][keyword] = {
            "exact_matches": exact_matches,
            "partial_matches": partial_matches,
            "total_matches": exact_matches + partial_matches,
            "frequency_percentage": round(frequency_percentage, 2),
            "contexts": contexts
        }
    
    # Calculate total matches across all keywords
    total_matches = sum(item["exact_matches"] for item in results["keywords"].values())
    results["total_matches"] = total_matches
    
    # Sort keywords by number of matches (descending)
    results["sorted_keywords"] = sorted(
        results["keywords"].items(),
        key=lambda x: x[1]["exact_matches"],
        reverse=True
    )
    
    return results

def find_related_terms(transcript, keywords, threshold=0.7):
    """
    Find terms in the transcript that might be related to the provided keywords.
    
    Args:
        transcript (str): Transcript text
        keywords (list): List of primary keywords
        threshold (float): Similarity threshold for considering words related
        
    Returns:
        dict: Dictionary with related terms for each keyword
    """
    if not transcript or not keywords:
        return {}
    
    # Extract all words from transcript
    words = re.findall(r'\b[a-z]{3,}\b', transcript.lower())
    
    # Count word frequencies
    word_counts = Counter(words)
    
    # Find related terms for each keyword
    related_terms = {}
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        related = []
        
        for word, count in word_counts.most_common(30):
            # Skip exact matches and very common words
            if word == keyword_lower:
                continue
                
            # Check if the word contains the keyword or vice versa
            if keyword_lower in word or word in keyword_lower:
                related.append({"term": word, "count": count, "relationship": "substring"})
            
            # Check if words frequently appear together
            # (This is a simplified approach - a more sophisticated approach would use context analysis)
            if count > 3 and len(word) > 3:
                # Look for co-occurrence pattern
                pattern = r'\b' + re.escape(keyword_lower) + r'\W+(?:\w+\W+){0,5}' + re.escape(word) + r'\b'
                co_occurrences = len(re.findall(pattern, transcript.lower()))
                
                if co_occurrences > 1:
                    related.append({
                        "term": word, 
                        "count": count, 
                        "relationship": "co-occurrence",
                        "co_occurrences": co_occurrences
                    })
        
        related_terms[keyword] = related[:10]  # Limit to top 10 related terms
    
    return related_terms 