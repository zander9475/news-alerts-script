from ..models.article import Article
from ..services.web_scraper import scrape_url
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Slot, QObject
from typing import Optional

class ArticleController(QObject):
    """
    Controls logic to perform CRUD operations on Articles. Communicates with ArticleManager
    """
    def __init__(self, model, view):
        super().__init__()
        self.model = model
        
    def _scrape_url_and_add(self, url: str, keyword: Optional[str] = None):
        """
        Private helper: Tries to scrape and add an article.

        @return tuple: (status, article_obj)
        """
        try:
            # Attempt to scrape, pass keyword in if coming from search results page
            article_dict = scrape_url(url)
            if keyword:
                article_dict['keyword'] = keyword

            # Create article object
            article = Article(**article_dict)

            # Attempt to add article to the model. Model returns status of article addition.
            was_added = self.model.add_article(article)

            return article, was_added
        except Exception as e:
            if 'login' in str(e):
                user_prompt = "Please attempt to login to the website.\nIf paywalled, add this article manually."
            else:
                user_prompt = "Please add this article manually."
            QMessageBox.critical(
                self.view,
                "Scrape Failed",
                f"Scrape failed: {e}\n\n{user_prompt}"
            )
            return None, None