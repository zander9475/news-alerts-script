from dataclasses import dataclass, field
import uuid
from typing import List, Optional

@dataclass
class Article:
    """
    Data class representing a single article.
    """
    title: str
    content: str
    source: str
    keyword: str = "Manual"
    author: List[str] = field(default_factory=list)
    url: Optional[str] = None
    lead: Optional[str] = None
    id: Optional[str] = None

    def __post_init__(self):
        """
        Generates unique ID for Article objects
        """
        if self.id is None:
            self.id = str(uuid.uuid4())

    def to_dict(self):
        """Converts the Article object to a dictionary."""
        return {
            "title": self.title,
            "lead": self.lead,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "author": self.author,
            "keyword": self.keyword
        }