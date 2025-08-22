from newspaper import Article, ArticleException # type:ignore
from titlecase import titlecase
import tldextract
from datetime import datetime
import sys
import requests
from fake_useragent import UserAgent
from utils import SOURCE_MAP
import re

class WebScraper:
    def __init__(self):
        self.source_map = SOURCE_MAP

        # Set user agent (to avoid website blocks)
        self.user_agent = UserAgent()

        # Set request headers
        self.headers = {
            "User-Agent": self.user_agent.random,
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _clean_author_string(self, authors_raw):
        """
        Cleans the raw author list from newspaper3k to remove duplicates and junk text.
        """
        if not authors_raw:
            return []

        cleaned_names = []
        junk_phrases = ["By", "From"]

        for raw_string in authors_raw:
            # Remove any junk phrases from the string
            for phrase in junk_phrases:
                raw_string = raw_string.replace(phrase, "")

            # Split the string in case a string contains multiple names
            # e.g. "John Smith and Jane Doe" becomes ["John Smith", "Jane Doe"]
            names = re.split(r'(?:,|and|&)', raw_string)

            # Add cleaned names to list
            for name in names:
                clean_name = name.strip()

                # Skip empty or long strings (likely not names)
                if not clean_name or len(clean_name.split()) > 5:
                    continue

                cleaned_names.append(clean_name)
                
        # Remove duplicates while preserving order
        unique_names = list(dict.fromkeys(cleaned_names))
        
        return unique_names

    def scrape_url(self, url):
        """
        Tries to scrape a single URL.
        Returns a dictionary of article data on success.
        Raises an ArticleException on failure.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'

            # Get html content
            html = response.text
            if not html.strip():
                raise ArticleException("Empty HTML returned")

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

            # Extract the base domain name from the URL
            source_domain = tldextract.extract(url).domain

            # Look up source domain in the map. If not found, use capitalized domain name.
            formatted_source = self.source_map.get(source_domain, source_domain.title())

            # Format date
            formatted_date = self._format_pub_date(article.publish_date)

            return {
                "title": capitalized_title,
                "author": cleaned_authors,
                "source": formatted_source,
                "pub_date": formatted_date,
                "content": article.text,
            }
        
        except requests.Timeout:
            raise ArticleException(f"Request to {url} timed out.")
        except requests.ConnectionError:
            raise ArticleException(f"Connection error — could not reach {url}.")
        except requests.HTTPError as e:
            raise ArticleException(f"HTTP error {e.response.status_code} — {e.response.reason} at {url}.")
        except requests.RequestException as e:
            raise ArticleException(f"Request failed — {e}")
        except ArticleException:
            raise
        except Exception as e:
            raise ArticleException(f"Unexpected error during scraping of {url}: {e}")
            
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

            # Format as M(M)/D(D)/YYYY string
            return dt.strftime(fmt)
        except Exception:
            return None