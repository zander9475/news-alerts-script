from jinja2 import Environment, FileSystemLoader
import smtplib
from email.message import EmailMessage
from utils import format_for_html

class EmailBuilder:
    def __init__(self, from_address: str, password: str):
        """
        Initializes the EmailBuilder.
        """
        self.env = Environment(loader=FileSystemLoader("templates"))
        self.template = self.env.get_template("email_template.html")
        self.from_address = from_address
        self.password = password

    @staticmethod
    def _send_email(subject: str, html_body: str, to_address: str, from_address: str, password: str):
        """
        Opens a new Outlook draft with the given subject and HTML body.
        """
        try:
            # Draft email
            email = EmailMessage()
            email['Subject'] = subject
            email['From'] = from_address
            email['To'] = to_address
            email.set_content(html_body)

            # Connect to Office 365's SMTP server and send email
            with smtplib.SMTP('smtp.office365.com', 587) as server:
                server.starttls() # Start TLS encryption
                server.login(from_address, password)
                server.send_message(email)

        except Exception as e:
            print(f"Error sending email: {e}")


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

            # Create and send email
            self._send_email(subject=subject, html_body=html, to_address="example@domain.com", from_address=self.from_address, password=self.password)
            
            return True
        
        except Exception as e:
            print(f"Failed to create draft for {article.title}. Error: {e}")
            return False