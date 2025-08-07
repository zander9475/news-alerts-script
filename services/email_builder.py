import pandas as pd
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from app.services.congress_scraper import get_congressional_activity
import ast
import os
import re
import win32com.client

def convert_paragraphs_to_html(text):
    """
    Converts text paragraphs (separated by newlines) to <br><br> for Outlook.
    Ensures consistent spacing between paragraphs.
    """
    if not isinstance(text, str):
        return text

    # Normalize all newline styles
    text = text.replace('\r\n', '\n')

    # Replace double newlines or more with <br><br>
    text = re.sub(r'\n\s*\n', '<br><br>', text)

    # Replace remaining single newlines with space (or another <br> if needed)
    text = re.sub(r'(?<!<br>)\n(?!<br>)', ' ', text)

    return text.strip()


def create_outlook_draft(subject, html_body):
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


def build_email():
    """
    Builds the final email from a template and article data.
    Returns True on success, False on failure.
    """
    try:
        # Load email template and article data
        filepath = "data/full_articles.csv"
        if not os.path.exists(filepath):
            print(f"Error: CSV file not found at {filepath}")
            return False
        
        df = pd.read_csv(filepath)

        # Convert the string representation of the list back to a Python list
        df['author'] = df['author'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        # Replace 'nan' in empty author column with empty string
        df['author'] =df['author'].fillna('')

        # Clean up and normalize content paragraphs for Outlook
        df['content'] = df['content'].apply(convert_paragraphs_to_html)

        # Get the congressional activity
        congress_activity = get_congressional_activity()

        # Load the Jinja2 email template
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("email_template.html")

        # Get today's date and format it as Month dd, yyyy (ex: July 21, 2025)
        current_date = datetime.now().strftime('%B %d, %Y')

        # Render HTML email content
        html = template.render(
            articles = df.to_dict(orient="records"),
            today_date = current_date,
            congress_activity = congress_activity
            )

        # Create the output directory if it doesn't exist
        if not os.path.exists("output"):
            os.makedirs("output")

        # Write HTML to a file
        with open("output/final_email.html", "w", encoding="utf-8") as f:
            f.write(html)

        # Create Outlook draft email
        create_outlook_draft(subject=f"BIS News Clips | {current_date}", html_body=html)
        
        return True
    
    except FileNotFoundError as e:
        print(f"Error building email: A required file was not found: {e}")
        return False
    
    except Exception as e:
        print(f"An unexpected error occurred while building the email: {e}")
        return False