#!/usr/bin/env python
"""
Interactive YouTube Whisper Analyzer
Run this script to use the tool with a nice interactive interface.
"""

import sys
from src.main import main
from src.cryptobanter import print_crypto_banter

if __name__ == "__main__":
    print_crypto_banter()
    print("Starting YouTube Whisper Analyzer in interactive mode...")
    
    # Add the interactive flag if not already present
    if '--interactive' not in sys.argv and '-i' not in sys.argv:
        sys.argv.append('--interactive')
    
    # Run the main function with the interactive flag
    exit(main()) 