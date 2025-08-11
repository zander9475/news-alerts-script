import trafilatura
from newspaper import Article, ArticleException
from titlecase import titlecase
import tldextract
import json
from datetime import datetime
import sys
import requests

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
    def __init__(self, user_agent=None):
        self.source_map = SOURCE_MAP
        self.tld_extractor = tldextract.TLDExtract()

        # Set user agent (to avoid website blocks)
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )

        # Common request headers for both tools
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _clean_author_string(self, authors_raw):
        """
        Cleans the raw author list from newspaper3k to remove duplicates and junk text.
        """
        if not authors_raw:
            return []

        cleaned_names = []
        junk_phrases = ["Updated On", "By"]

        # Loop through each string in the author list provided by newspaper3k
        for raw_string in authors_raw:
            # Remove any junk phrases from the string
            for phrase in junk_phrases:
                raw_string = raw_string.replace(phrase, "")

            # Split each string by commas in case it accidentally contains multiple names
            names = raw_string.split(',')

            # Add the cleaned names to cleaned names list
            for name in names:
                clean_name = name.strip()
                if clean_name:
                    cleaned_names.append(clean_name)
                
        # Remove duplicate names
        unique_names = []
        for name in cleaned_names:
            if name not in unique_names:
                unique_names.append(name)
                
        # Remove combined names (e.g. "John Doe Jane Smith")
        if len(unique_names) > 1:
            combined_names = []
            # Loop through list
            for name in unique_names:
                # For each name, loop through rest of list
                for other_name in unique_names:
                    # Combined name if name (outer loop) contains another name
                    if other_name in name and other_name != name:
                        combined_names.append(name)
            # Include only names not found in combined names
            final_names = [name for name in unique_names if name not in combined_names]
            return final_names
        
        return unique_names

    def scrape_url(self, url):
        """
        Tries live fetch first; if blocked or error, falls back to Google Cache.
        Returns article data dict on success, raises ArticleException on failure.
        """
        def fetch(url_to_fetch):
            """
            Fetches the URL and returns the HTML content.
            """
            try:
                response = requests.get(url_to_fetch, headers=self.headers)
                response.raise_for_status()
                html = response.text
                if not html.strip():
                    raise ArticleException("Empty HTML returned")
                return html
            except requests.RequestException as e:
                raise ArticleException(f"Could not fetch page: {e}")
        
        # Try live URL first
        try:
            html = fetch(url)
        except ArticleException as e_live:
            # On certain errors ('401', etc), try Google Cache fallback
            if isinstance(e_live.args[0], str) and any(code in e_live.args[0] for code in ['401', '403', '404']):
                cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
                try:
                    html = fetch(cache_url)
                except ArticleException as e_cache:
                    # Both failed
                    raise ArticleException(
                        f"Failed live URL ({e_live}) and Google Cache ({e_cache})"
                    )
            else:
                # Some other error: re-raise
                raise

        # Extract content with Newspaper3k
        article = Article(url)
        article.set_html(html)
        article.parse()
        
        if not article.text:
            raise ArticleException("Scrape resulted in no content")
        
        # Capitalize article title
        capitalized_title = titlecase(article.title) if article.title else None

        # Clean author list
        cleaned_authors = self._clean_author_string(article.authors)
        print (str(cleaned_authors))

        # Extract the base domain name from the URL
        source_domain = self.tld_extractor(url).domain

        # Look up source domain in the map. If not found, use capitalized domain name.
        formatted_source = self.source_map.get(source_domain, source_domain.title())
        print(formatted_source)

        # Formate date
        formatted_date = self._format_pub_date(article.publish_date)

        return {
            "title": capitalized_title,
            "author": cleaned_authors,
            "source": formatted_source,
            "pub_date": formatted_date,
            "content": article.text,
        }
            
    def _format_pub_date(self, publish_date):
        if not publish_date:
            return None 

        # If publish_date is a string, try to parse it
        if isinstance(publish_date, str):
            try:
                # Parse ISO 8601 string, handle 'Z' as UTC
                dt = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
            except Exception:
                return None
        elif isinstance(publish_date, datetime):
            dt = publish_date
        else:
            # Unknown type
            return None
        
        try:
            # Choose format based on platform
            if sys.platform.startswith('win'):
                fmt = '%#m/%#d/%Y'  # Windows
            else:
                fmt = '%-m/%-d/%Y'  # macOS/Linux

            # Format as M/D/YYYY
            return dt.strftime(fmt)
        except Exception:
            return None