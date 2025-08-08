import os
import json
from dotenv import load_dotenv
from app.services.google_searcher import GoogleSearcher
from app.services.web_scraper import WebScraper
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
    scraper = WebScraper()

    # Search articles and save metadata to csv file
    for item in searcher.search():
        # Normalize url for duplicate checking
        normalized = normalize_url(item['url'])

        # Check duplicates against current session and previous sessions
        if searcher.is_duplicate(normalized) or manager.is_duplicate(normalized):
            continue

        # Add normalized URL to item dict and session list
        item["normalized_url"] = normalized
        searcher.seen_urls.add(normalized)

        # Create article and save metadata
        article = Article(**item)
        manager.save_new_article(article)

if __name__ == "__main__":
    main()