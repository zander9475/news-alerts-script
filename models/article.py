from dataclasses import dataclass, field
import uuid
from typing import List, Optional

@dataclass
class Article:
    """
    Data class representing a single article.
    """
    title: str
    url: str
    normalized_url: str
    source: str
    keyword: str
    author: List[str] = field(default_factory=list)
    content: Optional[str] = None
    published_date: Optional[str] = None
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
            "source": self.source,
            "url": self.url,
            "normalized_url": self.normalized_url,
            "author": str(self.author),
            "keyword": self.keyword,
            "content": self.content if self.content is not None else "",
            "published_date": self.published_date if self.published_date is not None else ""
        }