import pandas as pd
from .article import Article
from ..utils import normalize_url
from typing import Optional
import ast
from titlecase import titlecase
from pandas.errors import EmptyDataError

class ArticleManager:
    """
    Manages the collection of all Article objects.
    """
    def __init__(self, filepath="data/seen_articles.csv"):
        """
        Initializes the ArticleModel.
        
        @param filepath (str): Path to the CSV file containing articles.
        """
        super().__init__()
        self.filepath = filepath
        self.csv_articles = self._load_from_csv
        self.seen_urls = set() # Keep a set of normalized URLs for fast lookup

    def _load_from_csv(self):
        """
        Private method: loads existing articles from the CSV file into a list of Article objects.
        """
        try:
            df = pd.read_csv(self.filepath)

            # Replace 'NaN' values with None for optional fields
            df['author'] = df['author'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
            df = df.where(pd.notna(df), None)

            # Initialize articles list
            articles = []

            # Create an Article object for each row in the dataframe
            for _, row in df.iterrows():
                article = Article(
                    title=row.get('title', ''),
                    content=row.get('content', ''),
                    source=row.get('source', ''),
                    url=row.get('url', ''),
                    keyword=row.get('keyword', ''),
                    author=row.get('author', []),
                    lead=row.get("lead", '')
                    )
                articles.append(article)
                # Populate the set of seen URLs
                if article.url:
                    self.seen_urls.add(normalize_url(article.url))              
        except FileNotFoundError:
            print(f"{self.filepath} not found. Starting with empty article list.")
            articles = []
        except EmptyDataError:
            print(f"{self.filepath} is empty. Starting with empty article list.")
            articles = []
        
        return articles

    def add_article(self, new_article):
        """
        Takes a new Article object and adds it to the list of Articles.
        Performs a duplicate check before adding.
        """
        # Enforce titlecase for title and source
        new_article.title = titlecase(new_article.title.strip())
        new_article.source = titlecase(new_article.source.strip())

        # First priority duplicate check: URL
        if new_article.url:
            url = normalize_url(new_article.url)
            # Check for duplicate
            if url in self.seen_urls:
                print(f'Duplicate article found: {new_article.title}')
                return False
        
        # If no url, check duplicate on title
        else:
            normalized_title = new_article.title.lower().strip()
            if normalized_title in self.seen_titles:
                print(f'Duplicate article found: {new_article.title}')
                return False
        
        # If not duplicate, add article to list
        self.articles.append(new_article)
        # Add url to seen urls
        if new_article.url:
            self.seen_urls.add(url)
        # Add title to seen titles
        self.seen_titles.add(new_article.title)
        
        self.articles_changed.emit()
        return True

    def save_article(self): # Needs to be redone
        """
        Saves Article object to .csv file.
        """
        if not self.articles:
            print("No articles to save.")
            return False
        
        try:
            # Convert each Article object in the list to a dictionary
            articles_as_dicts = [article.to_dict() for article in self.articles]

            # Create a DataFrame from the list of dictionaries
            df = pd.DataFrame(articles_as_dicts)

            # Save the DataFrame to the CSV file
            df.to_csv(self.filepath, index=False)

            print(f"Articles saved successfully to {self.filepath}")
            return True

        except FileNotFoundError:
            print(f"Error: The directory for '{self.filepath}' does not exist.")
            return False
        except PermissionError:
            print(f"Error: You do not have permission to write to '{self.filepath}'.")
            return False
        except Exception as e:
            # Catch any other unexpected errors
            print(f"An unexpected error occurred while saving: {e}")
            return False
