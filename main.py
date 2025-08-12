import os
import yaml
from dotenv import load_dotenv
from services.google_searcher import GoogleSearcher
from services.rss_fetcher import RssFetcher
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
    
    # Load config.yaml
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    rss_keywords = config.get('rss_keywords', [])
    api_keywords = config.get('api_keywords', [])
    rss_feeds = config.get('rss_feeds', {})
        
    # Initialize managers and services
    manager = DuplicateManager()
    searcher = GoogleSearcher(api_key=api_key, cse_id=cse_id, keywords=api_keywords)
    rss_fetcher = RssFetcher(rss_urls=rss_feeds, keywords=rss_keywords)
    scraper = WebScraper()
    builder = EmailBuilder()

    # Step 1: Search for new articles and save metadata
    session_articles = run_search(searcher, manager)

    # Step 1.5: RSS fetching
    rss_articles = run_rss_fetch(rss_fetcher, manager)

    # Combine Google search and RSS
    all_new_articles = session_articles + rss_articles

    if not all_new_articles:
        print("No new articles found. Exiting.")
        return

    # Step 2: Scrape articles
    for article in all_new_articles:
        handle_article_scrape(scraper, article)

    # Step 3: Build and send email
    for article in all_new_articles:
        builder.build_email(article)

def run_search(searcher, manager):
    """
    Calls searching service from GoogleSearcher. 
    Passes each article's url to the manager for duplicate checking and saving.
    """
    new_articles = []

    for article_data in searcher.search():
        # Normalize url and pass to DuplicateManager
        normalized = normalize_url(article_data['url'])
        if manager.add_url(normalized):
            # Add normalized url to article dictionary
            article_data["normalized_url"] = normalized

            # Create article object from dictionary and append to list
            article_obj = Article(**article_data)
            new_articles.append(article_obj)

    return new_articles

def run_rss_fetch(rss_fetcher, manager):
    """
    Calls RSS fetching service from RssFetcher.
    Passes each article's normalized url to the manager for duplicate checking and saving.
    """
    new_articles = []
    rss_articles = rss_fetcher.fetch_articles()
    for article in rss_articles:
        if manager.add_url(article.normalized_url):
            print(f"[run_rss_fetch] New article added: {article.normalized_url}")
            new_articles.append(article)

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