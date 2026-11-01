import hashlib
import urllib.parse
import requests
import feedparser
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from core.config import Config

class LiveEvidenceRetriever:
    """Connects exclusively to live public RSS feeds, Wikipedia REST API, GDELT, and DuckDuckGo."""

    @staticmethod
    def clean_html(raw_html: str) -> str:
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    @classmethod
    def fetch_live_rss_stream(cls, feed_url: str, source_label: str, max_items: int = 15) -> list:
        docs = []
        try:
            resp = requests.get(feed_url, headers=Config.HEADERS, timeout=8)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:max_items]:
                title = cls.clean_html(entry.get("title", ""))
                summary = cls.clean_html(entry.get("summary", entry.get("description", title)))
                link = entry.get("link", "")
                published = entry.get("published", entry.get("updated", "Live Feed"))
                if title and link:
                    doc_id = hashlib.md5(link.encode("utf-8")).hexdigest()
                    docs.append({
                        "doc_id": doc_id,
                        "title": title,
                        "summary": summary[:600],
                        "url": link,
                        "source_name": source_label,
                        "published_at": published
                    })
        except Exception as e:
            print(f"[LiveRSS Warning] {source_label}: {e}")
        return docs

    @classmethod
    def search_google_news_rss_live(cls, query: str, max_results: int = 6) -> list:
        encoded_q = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-IN&gl=IN&ceid=IN:en"
        return cls.fetch_live_rss_stream(url, "Google News Live Registry", max_items=max_results)

    @classmethod
    def search_duckduckgo_live(cls, query: str, max_results: int = 5) -> list:
        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, region="in-en", safesearch="off", max_results=max_results):
                    href = r.get("href", "")
                    title = r.get("title", "")
                    body = r.get("body", "")
                    if href and title:
                        results.append({
                            "doc_id": hashlib.md5(href.encode("utf-8")).hexdigest(),
                            "title": title,
                            "summary": body,
                            "url": href,
                            "source_name": "DuckDuckGo Live Web Index",
                            "published_at": "Real-Time Web"
                        })
        except Exception as e:
            print(f"[DDG Search Warning] {e}")
        return results

    @classmethod
    def search_wikipedia_live(cls, query: str, max_results: int = 3) -> list:
        results = []
        try:
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": max_results
            }
            r = requests.get(search_url, params=params, headers=Config.HEADERS, timeout=6)
            r.raise_for_status()
            search_items = r.json().get("query", {}).get("search", [])
            for item in search_items:
                title = item.get("title", "")
                snippet = cls.clean_html(item.get("snippet", ""))
                page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                results.append({
                    "doc_id": hashlib.md5(page_url.encode("utf-8")).hexdigest(),
                    "title": f"Wikipedia Knowledge Registry: {title}",
                    "summary": snippet,
                    "url": page_url,
                    "source_name": "Wikipedia REST Knowledge Graph",
                    "published_at": "Verified Encyclopedia"
                })
        except Exception as e:
            print(f"[Wikipedia API Warning] {e}")
        return results

    @classmethod
    def search_gdelt_live(cls, query: str, max_results: int = 4) -> list:
        results = []
        try:
            encoded_q = urllib.parse.quote(query)
            url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded_q}&mode=artlist&maxrecords={max_results}&format=json"
            r = requests.get(url, headers=Config.HEADERS, timeout=6)
            if r.status_code == 200:
                data = r.json()
                for art in data.get("articles", []):
                    art_url = art.get("url", "")
                    title = art.get("title", "")
                    domain = art.get("domain", "GDELT Global Monitor")
                    seendate = art.get("seendate", "Live GDELT")
                    if art_url and title:
                        results.append({
                            "doc_id": hashlib.md5(art_url.encode("utf-8")).hexdigest(),
                            "title": title,
                            "summary": f"Global media monitor record from {domain} (Timestamp: {seendate})",
                            "url": art_url,
                            "source_name": f"GDELT Live ({domain})",
                            "published_at": seendate
                        })
        except Exception as e:
            print(f"[GDELT API Warning] {e}")
        return results
