import feedparser
from models.article import Article
from utils import normalize_url
import time

class RssFetcher:
    def __init__(self, rss_urls, keywords):
        """
        Initialize with RSS feed URLs and keywords list.
        @param rss_urls: dict of {source_name: feed_url}
        @param keywords: list of keywords (strings)
        """
        self.rss_feeds = rss_urls
        self.keywords = [kw.lower() for kw in keywords]
        print(f"[RssFetcher] Initialized with {len(self.rss_feeds)} feeds and {len(self.keywords)} keywords.")

    def _match_keyword(self, text):
        """
        Returns the first keyword found in text (case-insensitive),
        or None if no keyword matches.
        """
        if not text:
            return None
        
        for keyword in self.keywords:
            if keyword in text.lower():
                print(f"[Keyword Match] Found keyword '{keyword}' in text.")
                return keyword
        return None
    
    def _entry_match_keyword(self, entry):
        """
        Check all relevant fields for keywords.
        Return the first matched keyword found, or None.
        """
        # Title
        matched = self._match_keyword(entry.get("title", ""))
        if matched:
            return matched
        
        # Summary or Description
        summary = entry.get("summary", "") or entry.get("description", "")
        matched = self._match_keyword(summary)
        if matched:
            return matched
        
        # content: sometimes feeds have a 'content' field with list of dicts having 'value'
        content_list = entry.get("content", [])
        for content_item in content_list:
            if isinstance(content_item, dict) and "value" in content_item:
                matched = self._match_keyword(content_item["value"])
                if matched:
                    return matched
        
        return None


    def fetch_articles(self):
        """
        Poll all RSS feeds, parse items, filter by keywords,
        return list of Article objects with minimal fields.
        """
        articles = []
        for source_name, feed_url in self.rss_feeds.items():
            print(f"[Fetch] Parsing RSS feed from source: {source_name}")
            try:
                feed = feedparser.parse(feed_url)
                sorted_entries = sorted(
                feed.entries,
                key=lambda e: e.get('published_parsed') or e.get('updated_parsed') or time.gmtime(0),
                reverse=True
                )
                print(f"[Fetch] Retrieved {len(sorted_entries)} entries from {source_name}.")
            except Exception as e:
                print(f"Failed to parse RSS feed {source_name}: {e}")
                continue

            for entry in sorted_entries:
                matched_keyword = self._entry_match_keyword(entry)
                if matched_keyword:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "") or entry.get("description", "")
                    link = entry.get("link", "")
                    normalized_url = normalize_url(link)

                    article = Article(
                        url=link,
                        normalized_url=normalized_url,
                        title=title,
                        source=source_name,
                        content=summary,
                        author=None,
                        pub_date=None,
                        keyword=matched_keyword
                    )
                    articles.append(article)

        print(f"[Fetch] Total matched articles collected: {len(articles)}")
        return articles