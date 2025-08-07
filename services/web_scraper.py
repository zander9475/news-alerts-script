from newspaper import Article, ArticleException
from titlecase import titlecase
import tldextract

def clean_author_string(authors_raw):
    """
    Cleans the raw author list from newspaper3k to remove duplicates and junk text.
    """
    if not authors_raw:
        return ""

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


def scrape_url(url):
    """
    Tries to scrape a single URL.
    Returns a dictionary of article data on success.
    Raises an ArticleException on failure.
    """
    try:
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

        article = Article(url, browser_user_agent = 'Mozilla/5.0')
        article.download()
        article.parse()
        
        if not article.text:
            raise ArticleException("Scrape resulted in no content")
        
        # Capitalize article title
        capitalized_title = titlecase(article.title) if article.title else "Untitled"

        # Clean author list
        cleaned_authors = clean_author_string(article.authors)

        # Extract the base domain name from the URL
        source_domain = tldextract.extract(url).domain

        # Look up source domain in the map. If not found, use capitalized domain name.
        formatted_source = SOURCE_MAP.get(source_domain, source_domain.title())

        return {
            "title": capitalized_title or "Untitled",
            "author": cleaned_authors,
            "source": formatted_source,
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