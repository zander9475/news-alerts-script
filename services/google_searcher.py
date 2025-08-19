import requests
from utils import is_potential_article

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

    def search(self):
            """
            Finds relevant articles using list of keywords, fetching all available pages of results.
            """
            articles = []
            for keyword in self.keywords:
                print(f"Searching for new articles for keyword: '{keyword}'...")
                start_index = 1 # Begin with first page

                while True:
                    try:
                        # Set API parameters
                        params = {
                            "key": self.api_key,
                            "cx": self.cse_id,
                            "q": keyword,
                            "dateRestrict": "d1",
                            "lr": "lang_en",
                            "start": start_index
                        }
                        # Query the API using session
                        response = self.session.get("https://www.googleapis.com/customsearch/v1", params=params)
                        response.raise_for_status()
                        search_results = response.json()

                        # Convert raw JSON response to a structured format
                        for item in search_results.get("items", []):
                            url = item["link"]
                            title = item.get("title", "")
                            source = item.get("displayLink", "")
                            is_valid_article, reason = is_potential_article(url, title)

                            # Skip non-articles and print the reason why
                            if not is_valid_article:
                                print(f"Skipping non-article ({reason}): {title} | {url}")
                                continue

                            # Add article
                            articles.append({
                                "title": title,
                                "url": url,
                                "source": source,
                                "keyword": keyword,
                            })

                        # Check if there is a next page of results
                        # 'nextPage': List containing a dictionary of attributes regarding the next page of results
                        next_page_info = search_results.get('queries', {}).get('nextPage')
                        if next_page_info:
                            # Pull the start index from the 'startIndex' key
                            start_index = next_page_info[0]['startIndex']
                            print(f"Found next page, starting search from result {start_index}")
                        else:
                            # No more pages for this keyword, break the while loop
                            print(f"No more pages found for '{keyword}'.")
                            break

                    except requests.exceptions.RequestException as e:
                        # Provide more detail for specific errors
                        if isinstance(e, requests.exceptions.HTTPError):
                            if e.response.status_code == 429:
                                print("Error: You have likely exceeded your daily API quota.")
                            else:
                                print(f"HTTP Error {e.response.status_code} ({e.response.reason})")
                        else:
                            print(f"A network error occurred: {e}")
                            
                        break

            if not articles:
                print("No new articles found across all keywords.")
        
            return articles