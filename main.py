import os
from dotenv import load_dotenv
from app.services.google_searcher import GoogleSearcher

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Initializes and runs the application.
    """
    # Get env variables
    api_key = os.getenv("API_KEY")
    cse_id = os.getenv("CSE_ID")
    if not api_key and not cse_id:
        raise ValueError("Environment variables not found in .env file")
    
    # Initialize searching service
    searcher = GoogleSearcher()

if __name__ == "__main__":
    main()