import pandas as pd
from .article import Article
import ast
from pandas.errors import EmptyDataError
import csv
import os

class DuplicateManager:
    """
    Manages the collection of all seen URLs for duplicate checking.
    """
    def __init__(self, filepath="data/seen_articles.csv"):
        """
        Initializes the DuplicateManager.
        @param filepath (str): Path to the CSV file containing articles.
        """
        self.filepath = filepath
        self.seen_urls = self._load_urls(self)

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
            self.seen_urls.add()
            
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(url + '\n')
            return True
        
        return False

    def _save_article(self, article):
        """
        Appends a single Article object to a .csv file.
        """
        # Get the article data as a dictionary
        article_dict = article.to_dict()

        # Define column order from dictionary keys
        fieldnames = list(article_dict.keys())

        # Check if file exists and is not empty
        file_exists = os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0

        try:
            # Open file in append mode ('a')
            with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
                # Use DictWriter to map dictionary keys to CSV columns
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # If file does not exist or is empty, write the header row
                if not file_exists:
                    writer.writeheader()

                # Write article data as a new row
                writer.writerow(article_dict)

            print(f"Article saved successfully to {self.filepath}")
            return True

        except (FileNotFoundError, PermissionError) as e:
            print(f"Error saving to '{self.filepath}': {e}")
            return False
        except Exception as e:
            # Catch any other unexpected errors
            print(f"An unexpected error occurred while saving: {e}")
            return False
