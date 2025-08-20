from urllib.parse import urlparse

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
    "ft": "Financial Times",
    "cnbc": "CNBC",
    "cnn": "CNN",
    "nbcnews": "NBC",
    "abcnews": "ABC",
    "bbc": "BBC",
    "usatoday": "USA TODAY",
    "foxbusiness": "Fox Business"
}

def normalize_url(url):
    """Strips a URL down to just domain and path for duplicate checking.
    Example: nytimes.com/2025/07/31/us/politics/white-house-ballroom-trump.html
    """
    if not url:
        return ""
    # Use urlparse to handle complex URLs safely
    parsed = urlparse(url)
    # Rebuild the URL with just the core domain and path
    # Removes http/https, www, query parameters, etc.
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path.rstrip('/') # remove trailing slash
    return f"{domain}{path}"

def is_potential_article(url, title):
    """
    Determines if a result is likely to be a news article using layered checks.
    Returns (True, "") if it's an article.
    Returns (False, "reason") if it is not.
    """
    parsed = urlparse(url)
    path = parsed.path.lower()
    title = title.lower()

    # --- RULE 1: High-Priority Exclusions ---
    high_priority_path_exclusions = [
        "/print-edition", "/digital-print-edition", "/subscribe", 
        "/stock-market" "/archive", "/home", "/index", "/category", 
        "/video", "/show", "/podcast", "/cnbc-latest-video-news", "/sitemap"
    ]
    for p in high_priority_path_exclusions:
        if p in path:
            return False, f"High-priority excluded path: '{p}'"
        
    high_priority_title_exclusions = [
        "sport", "stock market"
    ]

    for term in high_priority_title_exclusions:
        if term in title:
            return False, f"High-priority excluded title keyword: '{term}'"

    # --- RULE 2: Check for strong positive signals ---
    # If a URL has a date or a clear article pattern, approve it immediately.
    article_patterns = [
        "/article/", "/story/", "/post/", "/report/", "/202", 
        "/jan/", "/feb/", "/mar/", "/apr/", "/may/", "/jun/",
        "/jul/", "/aug/", "/sep/", "/oct/", "/nov/", "/dec/"
    ]
    if any(pattern in path for pattern in article_patterns):
        return True, ""

    # --- RULE 3: Check for general negative signals ---
    # Path-based exclusions (less critical than high-priority ones)
    excluded_paths = [
        "/user", "/author", "/tags", "/topic", "/section",
        "/profile", "/account", "/login", "/signup", "/register",
        "/about", "/contact", "/by", "/newsletter", "/people", 
        "/quotes", "/company", "/earnings", "/person" 
    ]
    for p in excluded_paths:
        if p in path:
            return False, f"Excluded path: '{p}'"

    # Title-based exclusions
    excluded_title_terms = [
        "sign up", "author:", "homepage", "your daily", "digest"
    ]
    for term in excluded_title_terms:
        if term in title:
            return False, f"Excluded title keyword: '{term}'"

    # --- RULE 4: Final structural checks ---
    if path.count('/') < 2:
        return False, "Path too shallow"
    if len(path) <= 20:
        return False, "Path too short"
    
    # If it passes all checks, assume it's an article.
    return True, ""

def format_for_html(text):
    """
    Converts text paragraphs (separated by newlines) to <br><br> for Outlook.
    """
    if not isinstance(text, str):
        return ""
    paragraphs = text.strip().split('\n')
    return '<br><br>'.join(p.strip() for p in paragraphs if p.strip())