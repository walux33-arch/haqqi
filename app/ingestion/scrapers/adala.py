"""Adala.ma scraper - البوابة القانونية لوزارة العدل المغربية.

Strategy:
1. Try Next.js __NEXT_DATA__ for static pages (resources, new_releases)
2. Try juriscassation.cspj.ma for court decisions (separate subdomain)
3. Fall back to manual URL input via admin UI
4. Use headless browser (Playwright) if available for JS-rendered search results
"""

import re
import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Optional

from app.ingestion.scrapers import BaseScraper, fetch_url, fetch_url_js, extract_nextjs_data, simple_html_to_text


class AdalaScraper(BaseScraper):
    name = "adala"
    label = "Adala.ma - وزارة العدل"
    base_url = "https://adala.justice.gov.ma"

    def scrape(self, keyword: str = "", max_items: int = 10) -> list[dict]:
        items = []

        # Method 1: Try static pages
        for page_path in ["/new_releases", "/resources"]:
            try:
                page_items = self._scrape_static_page(page_path, max_items)
                items.extend(page_items)
            except Exception as e:
                print(f"Static scrape {page_path} error: {e}")

        if len(items) >= max_items:
            return items[:max_items]

        # Method 2: Try juriscassation.cspj.ma
        try:
            juris_items = self._scrape_juriscassation(keyword, max_items - len(items))
            items.extend(juris_items)
        except Exception as e:
            print(f"Juriscassation scrape error: {e}")

        if len(items) >= max_items:
            return items[:max_items]

        # Method 3: Playwright for JS-rendered Adala search
        if keyword:
            try:
                js_items = self._scrape_with_playwright(keyword, max_items - len(items))
                items.extend(js_items)
            except Exception as e:
                print(f"Playwright scrape error: {e}")

        return items[:max_items]

    def _scrape_with_playwright(self, keyword: str, max_items: int) -> list[dict]:
        """Use Playwright to scrape JS-rendered search results from Adala."""
        search_url = f"{self.base_url}/search?q={urllib.parse.quote(keyword)}"
        html = fetch_url_js(search_url, timeout=30)
        if not html:
            return []

        items = []
        # Try extracting from __NEXT_DATA__ first (if page uses Next.js)
        data = extract_nextjs_data(html)
        if data:
            extracted = self._extract_from_nextjs(data, search_url)
            items.extend(extracted)

        # Fallback: extract text directly
        if not items:
            text = simple_html_to_text(html)
            if text and len(text) > 100:
                # Split into paragraphs and create items
                paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 100]
                for p in paragraphs[:max_items]:
                    items.append({
                        "title": f"Adala.ma - {keyword}",
                        "content": p[:3000],
                        "url": search_url,
                        "date": datetime.now().isoformat()[:10],
                        "doc_type": "judgement",
                    })

        return items[:max_items]

    def _scrape_static_page(self, path: str, max_items: int) -> list[dict]:
        """Scrape a Next.js static page by extracting __NEXT_DATA__."""
        url = f"{self.base_url}{path}"
        html = fetch_url(url)
        if not html:
            return []

        items = []

        # Try __NEXT_DATA__ first
        data = extract_nextjs_data(html)
        if data:
            extracted = self._extract_from_nextjs(data, url)
            items.extend(extracted)

        # Fallback: simple HTML text extraction
        if not items:
            text = simple_html_to_text(html)
            if text and len(text) > 100:
                items.append({
                    "title": f"Adala.ma - {path.strip('/')}",
                    "content": text[:3000],
                    "url": url,
                    "date": datetime.now().isoformat()[:10],
                    "doc_type": "judgement",
                })

        return items[:max_items]

    def _extract_from_nextjs(self, data: dict, source_url: str) -> list[dict]:
        """Extract content from Next.js __NEXT_DATA__ structure."""
        items = []
        try:
            props = data.get("props", {}).get("pageProps", {})
            # Walk through all values looking for lists of content
            self._walk_props(props, items, source_url)
        except Exception as e:
            print(f"Next.js extraction error: {e}")
        return items

    def _walk_props(self, obj: dict, items: list, source_url: str, depth: int = 0):
        """Recursively walk Next.js props to find content."""
        if depth > 5:
            return
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Detect content patterns
                if isinstance(value, str) and len(value) > 200 and any(kw in value for kw in ["القانون", "المادة", "قرار", "محكمة"]):
                    title_key = f"title_{key}" if key.startswith("content") else key
                    title = obj.get("title") or obj.get("name") or obj.get("titre") or ""
                    items.append({
                        "title": str(title)[:200] if title else f"محتوى {key}",
                        "content": value[:3000],
                        "url": source_url,
                        "date": obj.get("date") or obj.get("created_at") or datetime.now().isoformat()[:10],
                        "doc_type": "judgement",
                    })
                else:
                    self._walk_props(value, items, source_url, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                self._walk_props(item, items, source_url, depth + 1)

    def _scrape_juriscassation(self, keyword: str, max_items: int) -> list[dict]:
        """Try to scrape juriscassation.cspj.ma for court decisions."""
        juris_url = "https://juriscassation.cspj.ma"
        html = fetch_url(juris_url, timeout=10)
        if not html:
            return []

        items = []
        text = simple_html_to_text(html)
        if text and len(text) > 100:
            items.append({
                "title": "قرارات محكمة النقض - جوريسبريودانس",
                "content": text[:3000],
                "url": juris_url,
                "date": datetime.now().isoformat()[:10],
                "doc_type": "judgement",
            })
        return items[:max_items]

    def ingest_urls(self, urls: list[str]) -> list[dict]:
        """Ingest specific URLs from Adala.ma (manual input via admin)."""
        results = []
        for url in urls:
            html = fetch_url(url)
            if not html:
                results.append({"url": url, "status": "failed", "error": "غير متاح"})
                continue
            text = simple_html_to_text(html)
            if not text or len(text) < 50:
                results.append({"url": url, "status": "failed", "error": "نص فارغ"})
                continue
            try:
                doc = ingestion_pipeline.ingest_text(
                    text=text[:5000],
                    title=f"Adala.ma - {url.split('/')[-1][:50]}",
                    doc_type="judgement",
                )
                results.append({"url": url, "status": doc.status, "id": doc.id})
            except Exception as e:
                results.append({"url": url, "status": "failed", "error": str(e)})
        return results


class SGGScraper(BaseScraper):
    """SGG.ma scraper - الأمانة العامة للحكومة (الجريدة الرسمية)."""

    name = "sgg"
    label = "SGG.ma - الجريدة الرسمية"
    base_url = "https://www.sgg.gov.ma"
    arabic_url = "https://www.sgg.gov.ma/arabe"

    def scrape(self, keyword: str = "", max_items: int = 10) -> list[dict]:
        items = []

        # Method 1: Scrape Bulletin Officiel page for recent BO PDFs
        try:
            bo_items = self._scrape_bo_page(max_items)
            items.extend(bo_items)
        except Exception as e:
            print(f"SGG BO page error: {e}")

        if len(items) >= max_items:
            return items[:max_items]

        # Method 2: Scrape Legislation page
        try:
            leg_items = self._scrape_legislation_page(keyword, max_items - len(items))
            items.extend(leg_items)
        except Exception as e:
            print(f"SGG Legislation page error: {e}")

        if len(items) >= max_items:
            return items[:max_items]

        # Method 3: Search legislation
        if keyword:
            try:
                search_items = self._search_legislation(keyword, max_items - len(items))
                items.extend(search_items)
            except Exception as e:
                print(f"SGG search error: {e}")

        return items[:max_items]

    def _scrape_bo_page(self, max_items: int) -> list[dict]:
        """Scrape the Bulletin Officiel page for recent BO PDF links."""
        url = f"{self.arabic_url}/BulletinOfficiel.aspx"
        html = fetch_url(url)
        if not html:
            return []

        items = []
        # Find BO PDF links (pattern: /BO/AR/.../BO_*.pdf or /BO/AR/.../*.pdf)
        import re
        bo_links = re.findall(r'(/BO/AR/\d+/\d+/[^\"\']+\.pdf)', html)

        seen = set()
        for link in bo_links[:max_items]:
            if link in seen:
                continue
            seen.add(link)
            full_url = f"{self.base_url}{link}" if link.startswith("/") else link
            pdf_filename = link.split("/")[-1]

            items.append({
                "title": f"الجريدة الرسمية - {pdf_filename}",
                "content": f"الجريدة الرسمية: {full_url}",
                "url": full_url,
                "date": self._extract_date_from_bo_link(link),
                "doc_type": "law",
            })

        if not items:
            # Fallback: extract any text from the page
            text = simple_html_to_text(html)
            if text and len(text) > 100:
                items.append({
                    "title": "SGG.ma - الجريدة الرسمية",
                    "content": text[:3000],
                    "url": url,
                    "date": "",
                    "doc_type": "law",
                })

        return items[:max_items]

    def _extract_date_from_bo_link(self, link: str) -> str:
        """Try to extract date info from BO link path."""
        import re
        match = re.search(r'/BO/AR/\d+/(\d{4})/', link)
        if match:
            return match.group(1)
        return ""

    def _scrape_legislation_page(self, keyword: str, max_items: int) -> list[dict]:
        """Scrape the legislation listing page."""
        url = f"{self.arabic_url}/Legislation.aspx"
        html = fetch_url(url)
        if not html:
            return []

        items = []
        text = simple_html_to_text(html)
        if text and len(text) > 100:
            # If keyword, search within the text
            if keyword and keyword.lower() not in text.lower():
                return []
            items.append({
                "title": "SGG.ma - التشريعات",
                "content": text[:3000],
                "url": url,
                "date": "",
                "doc_type": "law",
            })
        return items[:max_items]

    def _search_legislation(self, keyword: str, max_items: int) -> list[dict]:
        """Search legislation using SGG search page."""
        import urllib.parse
        search_url = f"{self.arabic_url}/Legislation/rechercheSommairesBO.aspx?keyword={urllib.parse.quote(keyword)}"
        html = fetch_url(search_url)
        if not html:
            return []

        items = []
        text = simple_html_to_text(html)
        if text and len(text) > 100:
            items.append({
                "title": f"SGG.ma - بحث: {keyword}",
                "content": text[:3000],
                "url": search_url,
                "date": "",
                "doc_type": "law",
            })
        return items[:max_items]

    def ingest_urls(self, urls: list[str]) -> list[dict]:
        """Ingest specific URLs from SGG.ma (PDFs or pages)."""
        results = []
        for url in urls:
            html = fetch_url(url)
            if not html:
                results.append({"url": url, "status": "failed", "error": "غير متاح"})
                continue
            text = simple_html_to_text(html)
            if not text or len(text) < 50:
                results.append({"url": url, "status": "failed", "error": "نص فارغ"})
                continue
            try:
                doc = ingestion_pipeline.ingest_text(
                    text=text[:5000],
                    title=f"SGG.ma - {url.split('/')[-1][:50]}",
                    doc_type="law",
                )
                results.append({"url": url, "status": doc.status, "id": doc.id})
            except Exception as e:
                results.append({"url": url, "status": "failed", "error": str(e)})
        return results


class MandiliScraper(BaseScraper):
    """Mandili.net scraper for Moroccan legal codes (already in data/laws/)."""

    name = "mandili"
    label = "Mandili.net - المدونات القانونية"
    base_url = "https://mandili.net"

    def scrape(self, keyword: str = "", max_items: int = 10) -> list[dict]:
        # This source is already in data/laws/ via scripts/update_db.py
        # The scraper here is for any new content not yet indexed
        return []


# Registry of all scrapers
SCRAPERS = {
    "adala": AdalaScraper(),
    "sgg": SGGScraper(),
    "mandili": MandiliScraper(),
}
