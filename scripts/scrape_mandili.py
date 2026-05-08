"""Scrape all Moroccan law codes from mandili.net and load into JSON + ChromaDB"""
import httpx, json, os, re, sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "laws")
PDF_DIR = os.path.join(os.path.dirname(__file__), "data", "pdfs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

sys.path.insert(0, os.path.dirname(__file__))
from app.agent.legal_agent import chroma_client

LAW_SOURCES = {
    "penal": {
        "url": "https://mandili.net/code/1-59-413/",
        "name": "مجموعة القانون الجنائي",
        "article_pattern": "الفصل",
        "compound": True,
    },
    "doc": {
        "url": "https://mandili.net/code/12-08-1913/",
        "name": "قانون الالتزامات والعقود",
        "article_pattern": "الفصل",
        "compound": False,
    },
    "commercial": {
        "url": "https://mandili.net/code/15-95/",
        "name": "مدونة التجارة",
        "article_pattern": "المادة",
        "compound": False,
    },
    "family": {
        "url": "https://mandili.net/code/03-70/",
        "name": "مدونة الأسرة",
        "article_pattern": "المادة",
        "compound": False,
    },
    "labour": {
        "url": "https://mandili.net/code/65-99/",
        "name": "مدونة الشغل",
        "article_pattern": "المادة",
        "compound": False,
    },
}

def extract_articles_from_html(html_text, law_key, config):
    """Extract articles from mandili.net HTML"""
    articles = []
    
    # Remove <script> and <style> tags first
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    
    # Split by <p> tags
    p_tags = re.findall(r'<p[^>]*>(.*?)</p>', text, re.DOTALL)
    
    current_num = None
    current_text = []
    is_first_p = True  # skip header paragraphs
    
    for p_html in p_tags:
        clean = re.sub(r'<[^>]+>', '', p_html).strip()
        # Clean up HTML entities
        clean = clean.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        
        if not clean:
            continue
            
        # Skip header/footer metadata
        if is_first_p:
            # Skip date, author, title lines
            if re.match(r'^\d{4}-\d{2}-\d{2}$', clean) or 'wwwadmin' in clean:
                continue
            is_first_p = False
        
        # Check if this is an article header (الفصل X or المادة X)
        article_match = None
        if config["compound"]:
            # Handle compound numbers like "الفصل 1-35", "الفصل 1-44", "الفصل 2-35"
            article_match = re.match(r'^الفصل\s+(\d+[-–]\d+)$', clean)
            if not article_match:
                # Also handle simple الفصل numbers that may appear
                article_match = re.match(r'^الفصل\s+(\d+)$', clean)
        else:
            # Handle المادة X or الفصل X
            article_match = re.match(r'^(المادة|الفصل)\s+(\d+(?:[-–]\d+)*)$', clean)
            if article_match:
                # Return the number part (group 2)
                pass
        
        if article_match:
            # Save previous article if exists
            if current_num is not None and current_text:
                full_text = ' '.join(current_text).strip()
                articles.append({
                    "number": str(current_num),
                    "content": full_text,
                })
            
            current_num = article_match.group(1) if not config["compound"] else article_match.group(1)
            # For compound, also keep the group number
            if config["compound"] and article_match.lastindex and article_match.lastindex >= 2:
                current_num = article_match.group(1)
            current_text = []
        elif current_num is not None:
            # This is article content
            # Remove trailing references like "الفصل 1-35 أعلاه"
            current_text.append(clean)
    
    # Don't forget the last article
    if current_num is not None and current_text:
        full_text = ' '.join(current_text).strip()
        articles.append({
            "number": str(current_num),
            "content": full_text,
        })
    
    return articles


def download_and_extract(law_key, config):
    """Download law page and extract articles"""
    print(f"\n=== {config['name']} ({law_key}) ===")
    print(f"URL: {config['url']}")
    
    r = httpx.get(config["url"], follow_redirects=True, timeout=60)
    print(f"HTTP {r.status_code}, {len(r.text)} bytes")
    
    if r.status_code != 200:
        print(f"  FAILED: HTTP {r.status_code}")
        return None
    
    articles = extract_articles_from_html(r.text, law_key, config)
    print(f"  Extracted {len(articles)} articles")
    
    if not articles:
        print("  No articles found, saving debug HTML...")
        debug_path = os.path.join(os.path.dirname(__file__), f"debug_{law_key}.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(r.text)
        print(f"  Debug HTML saved to {debug_path}")
        return None
    
    # Save to JSON
    data = {"law": law_key, "articles": articles}
    json_path = os.path.join(DATA_DIR, f"{law_key}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {json_path}")
    
    return data


def load_to_chromadb(law_key, data):
    """Load articles into ChromaDB"""
    if not data or not data.get("articles"):
        print(f"  No articles to load for {law_key}")
        return
    
    from app.agent.legal_agent import LegalAgent
    agent = LegalAgent()
    
    collection = chroma_client.get_or_create_collection("moroccan_laws")
    
    articles = data["articles"]
    ids = []
    texts = []
    metadatas = []
    
    for art in articles:
        content = art.get("content", "").strip()
        num = art.get("number", "")
        if not content:
            continue
        ids.append(f"{law_key}_{num}")
        texts.append(content)
        metadatas.append({
            "law": law_key,
            "article_number": str(num),
            "chapter": "",
        })
    
    if texts:
        # Batch in groups of 100 to avoid memory issues
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch_end = min(i + batch_size, len(texts))
            collection.add(
                ids=ids[i:batch_end],
                documents=texts[i:batch_end],
                metadatas=metadatas[i:batch_end],
            )
        print(f"  Loaded {len(texts)} articles into ChromaDB")
    
    print(f"  Total in ChromaDB: {collection.count()}")


def main():
    all_articles = {}
    
    for law_key, config in LAW_SOURCES.items():
        data = download_and_extract(law_key, config)
        if data:
            all_articles[law_key] = data
            load_to_chromadb(law_key, data)
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    for law_key, data in all_articles.items():
        print(f"{configs[law_key]['name']}: {len(data['articles'])} articles")
    
    total = sum(len(d["articles"]) for d in all_articles.values())
    collection = chroma_client.get_collection("moroccan_laws")
    print(f"\nTotal extracted: {total} articles")
    print(f"Total in ChromaDB: {collection.count()}")

configs = LAW_SOURCES

if __name__ == "__main__":
    main()
