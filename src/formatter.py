"""
Module for formatting analysis results.
"""

import json

def format_results(analysis_results, format_type="text", include_contexts=True):
    """
    Format analysis results for output.
    
    Args:
        analysis_results (dict): Analysis results from analyzer
        format_type (str): Output format (text, json)
        include_contexts (bool): Whether to include matching contexts
        
    Returns:
        str: Formatted output
    """
    if format_type.lower() == "json":
        return json.dumps(analysis_results, indent=2)
    
    # Text format
    output = []
    
    # Add header
    output.append("=" * 60)
    output.append("YOUTUBE VIDEO TRANSCRIPT ANALYSIS")
    output.append("=" * 60)
    
    # Add summary stats
    output.append(f"Total words in transcript: {analysis_results.get('total_words', 0)}")
    output.append(f"Total keyword matches: {analysis_results.get('total_matches', 0)}")
    output.append("")
    
    # Check for errors
    if "error" in analysis_results:
        output.append(f"ERROR: {analysis_results['error']}")
        return "\n".join(output)
    
    # Add keyword details
    output.append("-" * 60)
    output.append("KEYWORD FREQUENCY ANALYSIS")
    output.append("-" * 60)
    
    # Use sorted keywords if available, otherwise use the keywords dictionary
    keywords_to_display = analysis_results.get("sorted_keywords", [])
    if not keywords_to_display and "keywords" in analysis_results:
        keywords_to_display = analysis_results["keywords"].items()
    
    # Display each keyword
    for keyword, data in keywords_to_display:
        output.append(f"\nKEYWORD: '{keyword}'")
        output.append(f"  Exact matches: {data['exact_matches']}")
        output.append(f"  Partial matches: {data['partial_matches']}")
        output.append(f"  Total matches: {data['total_matches']}")
        output.append(f"  Frequency: {data['frequency_percentage']}% of total words")
        
        # Add contexts if included
        if include_contexts and data['contexts']:
            output.append("\n  SAMPLE CONTEXTS:")
            for i, context in enumerate(data['contexts'], 1):
                output.append(f"  {i}. ...{context}...")
    
    # Add related terms if available
    if "related_terms" in analysis_results:
        output.append("\n" + "-" * 60)
        output.append("RELATED TERMS")
        output.append("-" * 60)
        
        for keyword, terms in analysis_results["related_terms"].items():
            output.append(f"\nTerms related to '{keyword}':")
            for term in terms:
                relationship = term.get("relationship", "")
                count = term.get("count", 0)
                output.append(f"  - {term['term']} (appears {count} times, {relationship})")
    
    # Add footer
    output.append("\n" + "=" * 60)
    
    return "\n".join(output)

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