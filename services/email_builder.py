from jinja2 import Environment, FileSystemLoader
import win32com.client
from utils import format_for_html

class EmailBuilder:
    def __init__(self):
        """
        Initializes the EmailBuilder.
        """
        self.env = Environment(loader=FileSystemLoader("templates"))
        self.template = self.env.get_template("email_template.html")

    @staticmethod
    def _create_outlook_draft(subject: str, html_body: str):
        """
        Opens a new Outlook draft with the given subject and HTML body.
        """
        try:
            outlook = win32com.client.Dispatch('Outlook.Application')
            mail = outlook.CreateItem(0)  # 0 = olMailItem
            mail.Subject = subject
            mail.HTMLBody = html_body
            mail.Display()  # Opens the draft for editing/sending
        except Exception as e:
            print(f"Error creating Outlook draft: {e}")


    def build_email(self, article):
        """
        Builds email html for a single article and creates outlook draft
        """
        try:
            # Prepare article's data for the template
            article_dict = article.to_dict()

            # Format content for html
            article_dict["content"] = format_for_html(article_dict["content"])

            # Render HTML email content
            html = self.template.render(
                article = article_dict
                )

            # Create subject line
            subject = f"NEWS ALERT: {article.title}"

            # Create Outlook draft email
            self._create_outlook_draft(subject=subject, html_body=html)
            
            return True
        
        except Exception as e:
            print(f"Failed to create draft for {article.title}. Error: {e}")
            return False