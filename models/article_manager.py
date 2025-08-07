import pandas as pd
from .article import Article
from ..utils import normalize_url
from PySide6.QtCore import Signal, QObject
from typing import Optional
import ast
from titlecase import titlecase
from pandas.errors import EmptyDataError

class ArticleManager(QObject):
    """
    Manages the collection of all Article objects.
    """
    # Custom signals
    articles_changed = Signal()
    article_updated = Signal(Article)

    def __init__(self, filepath="data/full_articles.csv"):
        """
        Initializes the ArticleModel.
        
        @param filepath (str): Path to the CSV file containing articles.
        """
        super().__init__()
        self.filepath = filepath
        self.articles = []
        self.seen_urls = set() # Keep a set of normalized URLs for fast lookup
        self.seen_titles = set() # Same thing for titles. This is for manual article duplicate checking
        self._load_articles()

    def _load_articles(self):
        """
        Private method: loads existing articles from the CSV file into a list of Article objects.
        """
        try:
            df = pd.read_csv(self.filepath)

            # Replace 'NaN values with None for optional fields
            df['author'] = df['author'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
            df = df.where(pd.notna(df), None)
            # Ensure 'lead' nan values are replaced with empty string
            df['lead'] = df['lead'].apply(lambda x: "" if x is None or pd.isna(x) else x)

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
                self.articles.append(article)
                # Populate the set of seen URLs
                if article.url:
                    self.seen_urls.add(normalize_url(article.url)) 
                # Populate the set of seen titles
                if article.title:
                    self.seen_titles.add(article.title.lower().strip())                 
        except FileNotFoundError:
            print(f"{self.filepath} not found. Starting with empty article list.")
            self.articles = []
        except EmptyDataError:
            print(f"{self.filepath} is empty. Starting with empty article list.")
            self.articles = []

    def get_all_articles(self):
        """Returns a list of all Article objects"""
        return self.articles
    
    def get_single_article(self, article_id: str) -> Optional[Article]:
        """
        Returns a single Article object by its unique ID.
        @param article_id (str): The unique ID of the article to retrieve.
        """
        for article in self.articles:
            if article.id == article_id:
                return article
                
        # If the loop finishes without finding a match, the article doesn't exist.
        return None
    
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
    
    def edit_article(self, article):
        """
        Edits an existing article by finding it with its unique ID.
        @param article (Article): The updated Article object. It MUST have a valid ID.
        """
        # Enforce titlecase for title and source
        article.title = titlecase(article.title.strip())
        article.source = titlecase(article.source.strip())

        for i, existing_article in enumerate(self.articles):
            if existing_article.id == article.id:
                # Found the article by ID, now replace it with the updated version
                self.articles[i] = article
                self.article_updated.emit(article)
                return True
                
        print(f"Error: Article with ID '{article.id}' not found for editing.")
        return False

    def delete_article(self, article):
        """
        Deletes an article from the Article list.
        @param article (Article): The Article object to be deleted. It MUST have a valid ID.
        """
        for i, existing_article in enumerate(self.articles):
            if existing_article.id == article.id:
                del self.articles[i]
                self.articles_changed.emit()
                return True

        print(f"Error: Article with ID '{article.id}' not found for deletion.")
        return False

    def reorder_articles(self, new_title_order):
        """
        Takes a list of titles in a new order and rearranges the Articles list to that order
        """
        # Create dictionary for article lookup
        article_mapper = {article.title: article for article in self.articles}

        # Create list for reordered articles
        reordered_articles = [article_mapper[title] for title in new_title_order]

        # Replace unordered list with ordered list
        self.articles = reordered_articles
        self.articles_changed.emit()


    def save_articles(self):
        """
        Saves the Article list as a CSV file, overwriting the old file.
        Returns True on success, False on failure.
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
