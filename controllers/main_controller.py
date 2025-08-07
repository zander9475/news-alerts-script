from .article_controller import ArticleController
from ..models.article_manager import ArticleManager
from ..views.widgets.search_dialog import SearchDialog
from ..services.google_searcher import search_articles
from ..services.email_builder import build_email
import os
from dotenv import load_dotenv
import json
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMessageBox

class MainController:
    """
    Controls top-level application logic (e.g. switching pages)
    """
    def __init__(self, view):
        # Store main window as instance attribute
        self.view = view

        # Create article manager
        self.model = ArticleManager()

        # Create article controller
        self.controller = ArticleController(self.model, self.view)

        # Ensure necessary directories exist
        os.makedirs("data", exist_ok=True)
        os.makedirs("output", exist_ok=True)

        # Connect signals
        self._connect_signals()

        # Load cached search results if available
        self._load_cached_results()

    def _connect_signals(self):
        """
        Connects signals from the view to controller methods.
        """
        # Main menu page signals
        self.view.main_menu_widget.search_requested.connect(self._show_search_dialog)
        self.view.main_menu_widget.search_results_page_requested.connect(lambda: self.view.switch_page("search_results"))
        self.view.main_menu_widget.articles_page_requested.connect(lambda: self.view.switch_page("article_management"))

        # Search results page signals
        self.view.search_results_widget.rerun_search_requested.connect(self._show_search_dialog)
        self.view.search_results_widget.main_menu_requested.connect(lambda: self.view.switch_page("main_menu"))
        self.view.search_results_widget.articles_page_requested.connect(lambda: self.view.switch_page("article_management"))

        # Article management page signals
        self.view.article_management_widget.main_menu_requested.connect(self._handle_main_menu_request_from_articles)
        self.view.article_management_widget.manual_input_requested.connect(lambda: self.view.switch_page("manual_input"))
        self.view.article_management_widget.save_articles_requested.connect(self._save_articles)

        # Manual input page signals
        self.view.manual_input_widget.submission_cancelled.connect(lambda: self.view.switch_page("article_management"))

    def _show_search_dialog(self):
        """Displays the search dialog for Google search."""
        dialog = SearchDialog(self.view)
    
        # Show the dialog and waits for the user to click OK or Cancel
        if dialog.exec(): 
            days_back = dialog.get_selected_days() # Get the value from the dialog
            # Pass the selected days back to the search handler
            self._handle_search(days_back)

    def _handle_search(self, days_back):
        """
        Handles the search operation by calling the search service and updating the view.
        """
        # Load API key and CSE ID from environment variables
        load_dotenv()
        api_key = os.getenv("API_KEY")
        cse_id = os.getenv("CSE_ID")

        # Load keywords from JSON file
        with open("keywords.json", "r") as f:
            keywords = json.load(f)["keywords"]

        if not keywords:
            print("No keywords provided for search.")
            return

        # Call the search service
        articles = search_articles(api_key, cse_id, keywords, days_back)

        # Save results to cache file
        with open("data/last_search_cache.json", "w") as f:
            json.dump(articles, f, indent=4)

        # Update the search results widget with the new articles
        self.view.search_results_widget.display_results(articles)
        
        # Switch to the search results page
        self.view.switch_page("search_results")

    def _load_cached_results(self):
        try:
            with open("data/last_search_cache.json", "r") as f:
                articles = json.load(f)
                if articles:
                    self.view.search_results_widget.display_results(articles)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is empty, do nothing
            pass

    @Slot()
    def _save_articles(self):
        """
        Calls model to save articles to csv file.
        Calls email formatter service to build email.
        """
        print("Saving articles...")
        # Save articles to .csv file
        save_success = self.model.save_articles()
        print(save_success)
        if save_success:
            # Build the email
            email_build_success = build_email()
            print(email_build_success)
            if email_build_success:
                # Success dialog
                QMessageBox.information(
                    self.view,
                    "Success",
                    "Outlook will now open with a draft of your email."
                )
            else:
                # Fail dialog
                QMessageBox.warning(
                    self.view,
                    "Build Failed",
                    "The attempt to build the email failed."
                )

    @Slot()
    def _handle_main_menu_request_from_articles(self):
        """
        Resets the article management view and switches to the main menu page.
        """
        # Call the reset method on the view
        self.view.article_management_widget.reset_view()

        # Then, switch the page
        self.view.switch_page("main_menu")