"""Scrape Moroccan law codes from mandili.net and save as JSON."""
import requests, re, json, os, sys, time
from bs4 import BeautifulSoup

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "laws")

CODES = {
    "criminal_procedure": {
        "url": "https://mandili.net/code/22-01/",
        "name": "قانون المسطرة الجنائية",
        "id": "criminal_procedure",
    },
}

def scrape_code(url, code_id, code_name):
    """Scrape articles from a mandili.net code page."""
    print(f"Fetching {code_name}...")
    r = requests.get(url, timeout=60)
    r.encoding = "utf-8"
    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    # Find the main content
    entry = soup.find("div", class_="entry-content")
    if not entry:
        entry = soup.find("article")
    if not entry:
        entry = soup.find("body")
    
    articles = []
    current_chapter = ""
    current_article_num = ""
    current_text = ""

    # Process all elements in order
    for el in entry.descendants:
        if el.name in ("h2", "h3", "h4"):
            # Save previous article if exists
            if current_article_num and current_text.strip():
                articles.append({
                    "number": current_article_num,
                    "chapter": current_chapter,
                    "content": current_text.strip(),
                })
                current_text = ""
            
            text = el.get_text(strip=True)
            # Check if this is a chapter/section heading
            if any(kw in text for kw in ["الباب", "الفصل", "القسم", "الفرع", "الباب الأول", "الباب الثاني"]):
                current_chapter = text
            # Check if this is an article heading
            art_match = re.match(r'المادة\s*(\d+(?:-\d+)?)', text)
            if art_match:
                current_article_num = art_match.group(1)
            else:
                # Maybe it's a subsection
                sec_match = re.match(r'(\d+(?:\.\d+)*)\s*[–-]?\s*(.+)', text)
                if sec_match and not any(kw in text for kw in ["الباب", "الفصل", "القسم"]):
                    current_article_num = sec_match.group(1)
        
        elif el.name == "p":
            text = el.get_text(strip=True)
            if not text:
                continue
            # Check if paragraph starts with article number
            art_match = re.match(r'المادة\s*(\d+(?:-\d+)?)\s*[–-]?\s*(.+)', text)
            if art_match:
                if current_article_num and current_text.strip():
                    articles.append({
                        "number": current_article_num,
                        "chapter": current_chapter,
                        "content": current_text.strip(),
                    })
                current_article_num = art_match.group(1)
                current_text = art_match.group(2)
            else:
                if current_article_num:
                    current_text += "\n" + text
                elif current_chapter:
                    current_text += "\n" + text

    # Save last article
    if current_article_num and current_text.strip():
        articles.append({
            "number": current_article_num,
            "chapter": current_chapter,
            "content": current_text.strip(),
        })

    # Deduplicate by article number
    seen = set()
    unique = []
    for a in articles:
        if a["number"] not in seen:
            seen.add(a["number"])
            unique.append(a)

    print(f"  Found {len(unique)} unique articles")
    
    # Save to JSON
    output = {
        "id": code_id,
        "name": code_name,
        "url": url,
        "articles": unique,
    }
    fpath = os.path.join(OUTPUT_DIR, f"{code_id}.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {fpath}")
    return unique

if __name__ == "__main__":
    for cid, info in CODES.items():
        try:
            scrape_code(info["url"], info["id"], info["name"])
            time.sleep(2)
        except Exception as e:
            print(f"Error scraping {info['name']}: {e}")
