import requests, re, json, sys, os
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

urls = {
    "criminal_procedure": "https://mandili.net/code/22-01/",
    "insurance": "https://mandili.net/code/17-99/",
    "credit": "https://mandili.net/code/103-12/",
    "copyright": "https://mandili.net/code/2-00/",
    "partnership": "https://mandili.net/code/5-96/",
    "societe_anonyme": "https://mandili.net/code/17-95/",
    "amo": "https://mandili.net/code/65-00/",
    "drugs_law": "https://mandili.net/code/1-73-282/",
    "military_service": "https://mandili.net/code/44-18/",
}

for name, url in urls.items():
    print(f"\n=== {name} ===")
    try:
        r = requests.get(url, timeout=30)
        html = r.text
        # Try to find articles - pattern: article number followed by content
        # Look for "المادة" or numbered sections
        articles = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', html)
        print(f"  Headings: {len(articles)}")
        
        # Also look for structured content in entry-content div
        match = re.search(r'class="entry-content[^"]*"[^>]*>(.*?)</div>\s*(?:</article|</div)', html, re.DOTALL)
        if match:
            content = match.group(1)
            # Extract paragraphs/divs with text
            texts = re.findall(r'<p[^>]*>(.*?)</p>', content)
            print(f"  Paragraphs: {len(texts)}")
            
            # Count article mentions
            art_count = len(re.findall(r'المادة\s+\d+', content))
            print(f"  Article mentions: {art_count}")
        else:
            print("  No entry-content found")
            # Try broader search
            content = html[html.find("<article"):html.find("</article>")] if "<article" in html else html[html.find("<body"):html.find("</body>")]
            art_count = len(re.findall(r'المادة\s+\d+', content))
            print(f"  Article mentions (broad): {art_count}")
    except Exception as e:
        print(f"  Error: {e}")
