"""
Sample script to run the YouTube Whisper Analyzer.
"""

import os
import sys

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in the project root
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded environment from .env file")
    else:
        print(f"No .env file found. You may need to create one from .env.template")
except ImportError:
    print("python-dotenv not installed. Install with: pip install python-dotenv")

from src.main import main

if __name__ == "__main__":
    # You can set the Groq API key in .env file instead of here
    # Check if API key is loaded from .env
    if not os.environ.get("GROQ_API_KEY"):
        print("\nWARNING: GROQ_API_KEY not found in environment variables or .env file.")
        print("You can set it in .env file or pass it using --api_key parameter.")
        print("See .env.template for the format.\n")
    
    # Run the main function
    exit(main()) 