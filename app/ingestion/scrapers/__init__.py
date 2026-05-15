"""Base scraper class for legal data sources."""

import os
import json
import hashlib
import time
from datetime import datetime
from typing import Optional
from app.ingestion import pipeline as ingestion_pipeline


SCRAPER_INDEX = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ingested", "scraper_index.json")
os.makedirs(os.path.dirname(SCRAPER_INDEX), exist_ok=True)


def _load_index():
    if os.path.exists(SCRAPER_INDEX):
        try:
            with open(SCRAPER_INDEX, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {}


def _save_index(index: dict):
    with open(SCRAPER_INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def _content_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()[:16]


def _is_duplicate(content_hash: str) -> bool:
    idx = _load_index()
    return content_hash in idx.get("seen", set())


def _mark_seen(content_hash: str, source: str, url: str):
    idx = _load_index()
    if "seen" not in idx:
        idx["seen"] = {}
    idx["seen"][content_hash] = {
        "source": source,
        "url": url,
        "scraped_at": datetime.now().isoformat(),
    }
    _save_index(idx)


def fetch_url(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch URL content with proper headers."""
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ar,fr;q=0.9,en;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"Fetch error for {url}: {e}")
        return None


def fetch_url_js(url: str, timeout: int = 30, headless: bool = True) -> Optional[str]:
    """Fetch URL content using Playwright (renders JS)."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        print(f"Playwright fetch error for {url}: {e}")
        return None


def extract_nextjs_data(html: str) -> Optional[dict]:
    """Extract __NEXT_DATA__ from Next.js pages (static/SSG only)."""
    import re
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def simple_html_to_text(html: str) -> str:
    """Minimal HTML to text conversion."""
    import re
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class BaseScraper:
    """Base class for all scrapers. Subclass and implement scrape()."""

    name: str = "base"
    label: str = "Base Scraper"
    base_url: str = ""

    def scrape(self, keyword: str = "", max_items: int = 10) -> list[dict]:
        """Return list of {title, content, url, date} dicts."""
        raise NotImplementedError

    def scrape_and_ingest(self, keyword: str = "", max_items: int = 10) -> dict:
        """Scrape, deduplicate, and ingest into pipeline."""
        items = self.scrape(keyword, max_items)
        results = {"total": len(items), "new": 0, "failed": 0, "items": []}
        for item in items:
            content = item.get("content", "")
            if not content:
                results["failed"] += 1
                continue
            ch = _content_hash(content)
            if _is_duplicate(ch):
                continue
            try:
                doc = ingestion_pipeline.ingest_text(
                    text=content,
                    title=item.get("title", ""),
                    doc_type=item.get("doc_type", "judgement"),
                )
                if doc.status == "completed":
                    _mark_seen(ch, self.name, item.get("url", ""))
                    results["new"] += 1
                    results["items"].append({
                        "id": doc.id,
                        "title": doc.title,
                        "status": doc.status,
                    })
                else:
                    results["failed"] += 1
            except Exception as e:
                print(f"Ingestion error: {e}")
                results["failed"] += 1
        return results

    def stats(self) -> dict:
        idx = _load_index()
        seen = idx.get("seen", {})
        source_items = {k: v for k, v in seen.items() if v.get("source") == self.name}
        return {"source": self.name, "total_scraped": len(source_items)}
