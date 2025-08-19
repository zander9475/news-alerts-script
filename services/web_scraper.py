from newspaper import Article, ArticleException # type:ignore
from titlecase import titlecase
import tldextract
from datetime import datetime
import sys
from playwright.sync_api import sync_playwright, Error as PlaywrightError
from fake_useragent import UserAgent

# Map domain names to source titles
SOURCE_MAP = {
    "foxnews": "Fox News",
    "reuters": "Reuters",
    "wsj": "Wall Street Journal",
    "apnews": "Associated Press",
    "washingtonpost": "Washington Post",
    "politico": "POLITICO",
    "nytimes": "New York Times",
    "bloomberg": "Bloomberg",
    "financialtimes": "Financial Times",
    "cnbc": "CNBC",
    "cnn": "CNN",
    "nbcnews": "NBC",
    "abcnews": "ABC",
    "bbc": "BBC",
    "usatoday": "USA TODAY",
    "foxbusiness": "Fox Business"
}

class WebScraper:
    def __init__(self):
        self.source_map = SOURCE_MAP
        self.tld_extractor = tldextract.TLDExtract()

        # Set user agent (to avoid website blocks)
        self.user_agent = UserAgent()

        # Set request headers
        self.headers = {
            "User-Agent": self.user_agent.random,
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Initialize Playwright and launch a persistent browser
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
            print("Playwright browser initialized successfully.")
        except Exception as e:
            print(f"Error initializing Playwright: {e}")

    def close(self):
        """Closes the browser and stops the Playwright instance."""
        if hasattr(self, 'browser') and self.browser:
            self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            self.playwright.stop()
        print("Playwright browser closed.")

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
        Tries to scrape a single URL.
        Returns a dictionary of article data on success.
        Raises an ArticleException on failure.
        """
        page = None
        try:
            page = self.browser.new_page(
                user_agent=self.headers["User-Agent"],
                headers={"Accept-Language": self.headers["Accept-Language"]}
            )
            
            # Navigate to URL
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Get html content
            html = page.content()
            if not html.strip():
                raise ArticleException("Empty HTML returned")

            # Detect possible bot-block pages
            block_indicators = [
                "captcha", "cloudflare", "access denied", "verify you are human",
                "restricted access", "bot protection"
            ]
            if any(indicator.lower() in html.lower() for indicator in block_indicators):
                raise ArticleException(f"Page may have blocked the bot — detected indicator in HTML: {url}")

            # Extract content with Newspaper4k
            article = Article(url)
            article.download(input_html=html)
            article.parse()
            
            if not article.text:
                raise ArticleException("Scrape resulted in no content")
            
            # Capitalize article title
            capitalized_title = titlecase(article.title) if article.title else None

            # Clean author list
            cleaned_authors = self._clean_author_string(article.authors)

            # Extract the base domain name from the URL
            source_domain = self.tld_extractor(url).domain

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
        
        except PlaywrightError as e:
            if "net::ERR_CONNECTION_REFUSED" in str(e):
                 raise ArticleException(f"Connection error — could not reach {url}.")
            elif "Timeout" in str(e):
                raise ArticleException(f"Request to {url} timed out via Playwright.")
            else:
                raise ArticleException(f"Playwright error for {url}: {e}")
        except ArticleException:
            raise
        except Exception as e:
            raise ArticleException(f"Unexpected error during scraping of {url}: {e}")
        finally:
            # Ensure page closes when done
            if page:
                page.close()
            
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