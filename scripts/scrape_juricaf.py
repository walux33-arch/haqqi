"""Scrape Moroccan Cour de cassation decisions from juricaf.org RSS.
Only 30 most recent available (RSS pagination blocked by Anubis anti-bot).
"""
import os, time, json, xml.etree.ElementTree as ET, httpx, re

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "judgements")
BASE_URL = "https://juricaf.org/recherche/+/facet_pays:Maroc"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch_page(url):
    r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=30)
    r.raise_for_status()
    return r.content

def fix_xml(content):
    """Fix malformed XML by escaping unescaped & in URLs"""
    text = content.decode("utf-8")
    # Fix & that aren't already escaped
    text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;)", "&amp;", text)
    return text.encode("utf-8")

def parse_rss(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.iter("item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub_date = item.findtext("pubDate", "")
        description = item.findtext("description", "")
        chamber = ""
        desc_text = description or ""
        for line in desc_text.split("\n"):
            if "Chambre" in line or "chambre" in line:
                chamber = line.strip()
                break
        items.append({
            "title": title.strip() if title else "",
            "link": link.strip() if link else "",
            "date": pub_date.strip() if pub_date else "",
            "chamber": chamber,
            "description": desc_text.strip(),
        })
    return items

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_decisions = []

    # Fetch first page (no start param) - always works
    xml_bytes = fetch_page(BASE_URL + "?format=rss")
    items = parse_rss(xml_bytes)
    all_decisions.extend(items)
    print(f"Page 1 (no start): {len(items)} decisions")

    # Try subsequent pages with start param
    for start in range(30, 120, 30):
        url = f"{BASE_URL}?start={start}&format=rss"
        try:
            content = fetch_page(url)
            # Check if it's HTML (bot challenge) vs XML
            if content.startswith(b"<!doctype") or content.startswith(b"<html"):
                print(f"  start={start}: bot challenge page, stopping")
                break
            fixed = fix_xml(content)
            items = parse_rss(fixed)
            all_decisions.extend(items)
            print(f"  start={start}: {len(items)} decisions (total: {len(all_decisions)})")
        except Exception as e:
            print(f"  start={start}: {e}, stopping")
            break
        time.sleep(1)

    output_path = os.path.join(OUTPUT_DIR, "juricaf_decisions.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_decisions, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(all_decisions)} decisions to {output_path}")

if __name__ == "__main__":
    main()
