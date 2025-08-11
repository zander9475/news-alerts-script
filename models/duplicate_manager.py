import os

class DuplicateManager:
    """
    Manages the collection of all seen URLs for duplicate checking.
    """
    def __init__(self, filepath="data/seen_urls.txt"):
        """
        Initializes the DuplicateManager.
        @param filepath (str): Path to the CSV file containing articles.
        """
        self.filepath = filepath
        self.seen_urls = self._load_urls()

    def _load_urls(self):
        """
        Private method: loads existing urls from a CSV file
        """
        if not os.path.exists(self.filepath):
            return set()
        with open(self.filepath, 'r', encoding='utf-8') as f:
            # Read all lines and strip whitespace/newlines
            return {line.strip() for line in f}
    
    def _is_duplicate(self, normalized_url: str):
        """
        Checks if a url is a duplicate.
        """
        return normalized_url in self.seen_urls

    def add_url(self, url):
        """
        Adds a new URL to the set and appends it to the file, if not already a duplicate
        """
        if not self._is_duplicate(url):
            self.seen_urls.add(url)

            # Ensure the directory exists before trying to open the file
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            
            # Add url to the file
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(url + '\n')
            return True
        
        return False
