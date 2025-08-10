import requests
from ..utils import is_potential_article

class GoogleSearcher:
    def __init__(self, api_key: str, cse_id: str, keywords: list):
        """
        Initializes the searcher.

        @ param api_key: Your Google API key.
        @ param cse_id: Your Custom Search Engine ID.
        @ param keywords: A list of keywords to search.
        """
        # Initialize instance attributes
        self.api_key = api_key
        self.cse_id = cse_id
        self.keywords = keywords
        
        # Create a Session object for multiple calls to API (HTTP Keep-Alive)
        self.session = requests.Session()

    def search(self): # Eventually change to loop over keyword till no articles found
        """
        Finds relevant articles using list of keywords
        """
        articles = []
        for keyword in self.keywords:
            print(f"Searching for new articles for keyword: '{keyword}'...")
            try:
                # Set API parameters
                params = {
                    "key": self.api_key,
                    "cx": self.cse_id,
                    "q": keyword,
                    "dateRestrict": "d1"
                }
                # Query the API using session
                response = self.session.get("https://www.googleapis.com/customsearch/v1", params=params)
                response.raise_for_status()

                # Convert raw JSON response to a structured format
                for item in response.json().get("items", []):
                    url = item["link"]
                    title = item.get("title", "")
                    is_valid_article, reason = is_potential_article(url, title)

                    # Skip non-articles and print the reason why
                    if not is_valid_article:
                        print(f"Skipping non-article ({reason}): {title} | {url}")
                        continue

                    # Add article
                    articles.append({
                        "title": item["title"],
                        "url": item["link"],
                        "keyword": keyword,
                    })

            except requests.exceptions.RequestException as e:
                # Provide more detail for specific errors
                if isinstance(e, requests.exceptions.HTTPError):
                    if e.response.status_code == 429:
                        print("  > Reason: You have likely exceeded your daily API quota.")
                    else:
                        print(f"  > Reason: HTTP Error {e.response.status_code} ({e.response.reason})")
                else:
                    print(f"  > Reason: A network error occurred: {e}")
                    
                continue

        if not articles:
            print("No new articles found across all keywords.")
       
        return articles
