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
        self.view = view
        self._connect_signals()

        # Load existing articles to article management page
        self._refresh_articles_view()

    def _connect_signals(self):
        # Search results page signals
        self.view.search_results_widget.article_addition_requested.connect(self.handle_search_result_add)

        # Article management page signals
        self.view.article_management_widget.url_scrape_requested.connect(self._handle_manual_url_add)
        self.view.article_management_widget.article_preview_requested.connect(self._show_article_preview)
        self.view.article_management_widget.edit_article_requested.connect(self._handle_article_edit_request)
        self.view.article_management_widget.delete_article_requested.connect(self._handle_article_delete_request)

        # Manual input page signals
        self.view.manual_input_widget.submission_completed.connect(self._handle_manual_submission)

        # Article manager model signals
        self.model.articles_changed.connect(self._refresh_articles_view)
        self.model.article_updated.connect(self._update_single_article_view)

    @Slot()
    def _refresh_articles_view(self):
        articles = self.model.get_all_articles()
        self.view.article_management_widget.populate_list(articles)

    @Slot(Article)
    def _update_single_article_view(self, article):
        """
        Updates the display text of edited article in the preview pane
        @param article: edited Article object
        """
        # Refresh display
        self.view.article_management_widget.update_preview(article)

        # Refresh listbox
        self._refresh_articles_view()

    @Slot(dict)
    def handle_search_result_add(self, result_data: dict):
        """
        Adds an article added by the user through the "Add to Email" button on the search results page
        
        @param result_data (dict): A dictionary of the article's data so far (title, url, source, keyword)
        """
        # Fetch the url and keyword
        url = result_data.get("url")
        keyword = result_data.get("keyword")
        if not (url and keyword): return

        # Call the helper, which returns the article and its addition status
        article, was_added = self._scrape_url_and_add(url, keyword)

        if article and was_added:
            # Success dialog
            QMessageBox.information(
                self.view, 
                "Success", 
                f"'{article.title}' was successfully added."
            )
        elif article and not was_added:
            # Duplicate error dialog
            QMessageBox.warning(
                self.view, 
                "Duplicate Article", 
                f"'{article.title}' is already in your collection."
            )

    @Slot(str)
    def _handle_manual_url_add(self, url: str):
        """
        Adds an article entered by the user through the URL field in the article management page

        @param url (str): The url of the article
        """
        article, was_added = self._scrape_url_and_add(url)

        if article and was_added:
            # Success dialog
            QMessageBox.information(
                self.view, 
                "Success", 
                f"'{article.title}' was successfully added."
            )
        elif article and not was_added:
            # Duplicate error dialog
            QMessageBox.warning(
                self.view, 
                "Duplicate Article", 
                f"'{article.title}' is already in your collection."
            )

    @Slot(Article)
    def _handle_manual_submission(self, article: Article):
        """
        Handles a submission from the manual input form (could be add or edit).
        The ManualInputWidget decides if it's an add or edit and passes the appropriate Article object.
        """
        # Handle edit submission
        # Check if passed in article has id AND if an article with that id already exists
        if article.id and self.model.get_single_article(article.id):
            was_updated = self.model.edit_article(article)
            if was_updated:
                # Success dialog
                QMessageBox.information(
                    self.view,
                    "Success",
                    f"'{article.title}' was successfully updated."
                )
            else:
                # Fail dialog
                QMessageBox.warning(
                    self.view,
                    "Update Failed",
                    f"Failed to update '{article.title}'. Article not found."
                )
        
        else:
            successful_add = self.model.add_article(article)
            if successful_add:
                # Success dialog
                QMessageBox.information(
                    self.view, 
                    "Success", 
                    f"'{article.title}' was successfully added."
                )
            else:
                # Duplicate error dialog
                QMessageBox.warning(
                    self.view, 
                    "Duplicate Article", 
                    f"'{article.title}' is already in your collection."
                )

        # Upon success or fail, switch back to article management page
        self.view.switch_page("article_management")

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
        
    def _show_article_preview(self, article):
        """
        Retrieves article from view. Updates preview pane with that article.
        @param article (Article): The article to be displayed.
        """
        if article:
            self.view.article_management_widget.update_preview(article)

    @Slot(Article)
    def _handle_article_edit_request(self, article: Article):
        """
        Opens a pane to edit an existing article and updates the model if changes are saved.
        """
        if not article:
            return
        
        # Prepare the manual input widget for editing
        self.view.manual_input_widget.set_article_data(article)
        
        # Switch to the manual input page
        self.view.switch_page("manual_input")

    @Slot(Article)
    def _handle_article_delete_request(self, article: Article):
        """Calls function on model to delete article"""
        self.model.delete_article(article)