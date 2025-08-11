import os
import json
from dotenv import load_dotenv
from services.google_searcher import GoogleSearcher
from services.web_scraper import WebScraper
from utils import normalize_url
from models.duplicate_manager import DuplicateManager
from models.article import Article
from services.email_builder import EmailBuilder

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Initializes and runs the application.
    """
    # Get env variables
    api_key = os.getenv("API_KEY")
    cse_id = os.getenv("CSE_ID")
    if not api_key or not cse_id:
        raise ValueError("Environment variables not found in .env file")
    
    # Get keywords
    with open('keywords.json', 'r', encoding='utf-8') as f:
        keywords = json.load(f)
        
    # Initialize session objects
    searcher = GoogleSearcher(api_key=api_key, cse_id=cse_id, keywords=keywords)
    manager = DuplicateManager()
    scraper = WebScraper()
    builder = EmailBuilder()

    # Step 1: Search for new articles and save metadata
    session_articles = run_search(searcher, manager)

    # Check if list of articles is empty and exit program if it is
    if not session_articles:
        print("No new articles found. Exiting.")
        return

    # Step 2: Scrape articles
    for article in session_articles:
        handle_article_scrape(scraper, article)

    # Step 3: Build and send email
    for article in session_articles:
        builder.build_email(article)

def run_search(searcher, manager):
    """
    Calls searching service from GoogleSearcher. 
    Passes each article's url to the manager for duplicate checking and saving.
    """
    new_articles = []

    for article_data in searcher.search():
        # Normalize url and pass to DuplicateManager
        # DuplicateManager's add_url() returns true if not duplicat
        normalized = normalize_url(article_data['url'])
        is_new_article = manager.add_url(normalized)

        if is_new_article:
            # Add normalized url to article dictionary
            article_data["normalized_url"] = normalized

            # Create article object from dictionary and append to list
            article_obj = Article(**article_data)
            new_articles.append(article_obj)

    return new_articles

def handle_article_scrape(scraper, article):
    """
    Passes article's URL to scraping service.
    If scrape successful, adds new fields and passes to manager for saving.
    """
    try:
        # Attempt to scrape
        article_data = scraper.scrape_url(article.url)
        
        # Add/update article fields
        if article_data["title"] is not None:
            article.title = article_data["title"]
        article.source = article_data["source"]
        article.author = article_data["author"]
        article.pub_date = article_data["pub_date"]
        article.content = article_data["content"]
        print(f"Successfully scraped: {article.title}")

    except Exception as e:
        print(f"Failed to scrape {article.title}. Reason: {e}")


if __name__ == "__main__":
    main()