import os
import json
from dotenv import load_dotenv
from app.services.google_searcher import GoogleSearcher
from utils import normalize_url
from app.models.article_manager import ArticleManager
from app.models.article import Article


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
    
    # Get keywords
    with open('keywords.json', 'r', encoding='utf-8') as f:
        keywords = json.load(f)
        
    # Initialize session objects
    searcher = GoogleSearcher(api_key=api_key, cse_id=cse_id, keywords=keywords)
    manager = ArticleManager()

    # Search articles
    for item in searcher.search():
        # Normalize url for duplicate checking
        normalized = normalize_url(item['url'])

        # Check duplicates against current session
        if searcher.is_duplicate(normalized):
            continue
        # Check duplicates against previous sessions
        if manager.is_duplicate(normalized):
            continue

        # Add normalized URL to item dict and session list
        item["normalized_url"] = normalized
        searcher.seen_urls.add(normalized)

        # Create and save article
        article = Article(**item)
        manager.save_new_article(article)

if __name__ == "__main__":
    main()