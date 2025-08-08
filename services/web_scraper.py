import trafilatura
from newspaper import Article, ArticleException
from titlecase import titlecase
import tldextract
import json
from datetime import datetime
import sys

# Map domain names to source titles
SOURCE_MAP = {
    "apnews": "Associated Press",
    "nytimes": "New York Times",
    "wsj": "Wall Street Journal",
    "politico": "POLITICO",
    "ft": "Financial Times",
    "cnbc": "CNBC",
    "scmp": "South China Morning Post",
    "foxnews": "Fox News",
    "washingtonpost": "Washington Post",
    "cnn": "CNN",
    "bloomberglaw": "Bloomberg"

}

class WebScraper:
    def __init__(self):
        self.source_map = SOURCE_MAP
        self.tld_extractor = tldextract.TLDExtract()

    def scrape_url(self, url):
        """
        Tries to scrape a single URL.
        Returns a dictionary of article data on success.
        Raises an ArticleException on failure.
        """
        try:
            # Fetch raw HTML using Trafilatura
            html = trafilatura.fetch_url(url)
            if not html:
                raise ArticleException("Could not fetch page")
            
            # Extract metadata (trafilatura)
            meta_json = trafilatura.extract(html, include_meta=True, output_format='json')
            meta = json.loads(meta_json) if meta_json else {}

            # Extract content with Newspaper3k
            article = Article(url, browser_user_agent = 'Mozilla/5.0')
            article.download()
            article.parse()
            
            if not article.text:
                raise ArticleException("Scrape resulted in no content")
            
            # Capitalize article title
            raw_title = meta.get('title', '')
            capitalized_title = titlecase(raw_title) if raw_title else "Untitled"

            # Extract the base domain name from the URL
            source_domain = self.tld_extractor(url).domain

            # Look up source domain in the map. If not found, use capitalized domain name.
            formatted_source = self.source_map.get(source_domain, source_domain.title())

            return {
                "title": capitalized_title or "Untitled",
                "author": meta.get('author', ''),
                "source": formatted_source,
                "published_date": self.format_pub_date(meta),
                "content": article.text,
                "url": url
            }
        except Exception as e:
            if '404' in str(e):
                raise ArticleException("This url either does not exist, or the website blocks web scraping by bots." \
                                        "\nClick title to verify if article exists.")
            elif '403' in str(e):
                raise ArticleException("This website does not allow web scraping by bots.")
            elif '401' in str(e):
                raise ArticleException("This article is paywalled or requires a login\n(Usually a Google sign-in).")
            else:
                # For all other errors, re-raise the original exception
                raise ArticleException(e)
            
    def format_pub_date(self, meta):
        date_str = meta.get('date')
        if not date_str:
            return None 

        try:
            # Parse the ISO 8601 date string
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))  # handle 'Z' as UTC

            # Choose format based on platform
            if sys.platform.startswith('win'):
                fmt = '%#m/%#d/%Y'  # Windows
            else:
                fmt = '%-m/%-d/%Y'  # macOS/Linux

            # Format as M/D/YYYY
            formatted_date = dt.strftime(fmt)
            return formatted_date
        except Exception:
            return None