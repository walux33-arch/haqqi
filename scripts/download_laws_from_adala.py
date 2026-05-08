"""Download Moroccan laws from adala.justice.gov.ma API.

API base: https://adala.justice.gov.ma/api/folders/12
  - 21: penal
  - 19: DOC (obligations & contracts)
  - 22: family
  - 57: social/labour
"""

import os
import re
import json
import httpx
import fitz

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
LAWS_DIR = os.path.join(DATA_DIR, "laws")
PDF_DIR = os.path.join(LAWS_DIR, "pdfs")
API_BASE = "https://adala.justice.gov.ma/api/folders/12"

LAW_FOLDERS = {
    "penal": 21,
    "doc": 19,
    "commercial": 23,
    "family": 22,
    "labour": 57,
}

# v2 regex: handles Arabic word numerals + digit patterns
ARTICLE_PATTERN = re.compile(
    r"(?:المادة|الفصل|Art\.?|Article)\s*(?:\d+(?:\s*-\s*\d+)?|الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|الحادي\s*عشر|الثاني\s*عشر|الثالث\s*عشر|الرابع\s*عشر|الخامس\s*عشر|السادس\s*عشر|السابع\s*عشر|الثامن\s*عشر|التاسع\s*عشر|العشرون|الثلاثون|الأربعون|الخمسون|الستون|السبعون|الثمانون|التسعون|المائة)\s*[:\-]?\s*",
    re.IGNORECASE
)


def fetch_pdf(folder_id: int, law_name: str) -> bytes | None:
    url = f"{API_BASE}/{folder_id}"
    r = httpx.get(url, timeout=30)
    if r.status_code != 200:
        print(f"  API error for {law_name}: {r.status_code}")
        return None
    data = r.json()
    files = data.get("files", data.get("data", []))
    if not files:
        print(f"  No files found for {law_name}")
        return None
    pdf_url = files[0].get("url", files[0].get("link", ""))
    if not pdf_url:
        print(f"  No PDF URL for {law_name}")
        return None
    pdf_r = httpx.get(pdf_url, timeout=60)
    if pdf_r.status_code != 200:
        print(f"  PDF download error for {law_name}: {pdf_r.status_code}")
        return None
    return pdf_r.content


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def parse_articles(text: str) -> list:
    articles = []
    parts = ARTICLE_PATTERN.split(text)
    if len(parts) < 2:
        return articles
    for i in range(1, len(parts), 2):
        article_num = parts[i - 1] if i - 1 < len(parts) else ""
        content = parts[i].strip() if i < len(parts) else ""
        articles.append({"number": article_num.strip(), "content": content[:2000]})
    return articles


def main():
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(LAWS_DIR, exist_ok=True)

    for law_name, folder_id in LAW_FOLDERS.items():
        print(f"\nProcessing {law_name} (folder {folder_id})...")
        pdf_bytes = fetch_pdf(folder_id, law_name)
        if not pdf_bytes:
            print(f"  SKIP: could not fetch {law_name}")
            continue

        pdf_path = os.path.join(PDF_DIR, f"{law_name}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"  PDF saved ({len(pdf_bytes)} bytes)")

        text = extract_text_from_pdf(pdf_bytes)
        articles = parse_articles(text)
        print(f"  Extracted {len(articles)} article-like sections")

        output_path = os.path.join(LAWS_DIR, f"{law_name}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"law": law_name, "articles": articles}, f, ensure_ascii=False, indent=2)
        print(f"  Saved to {output_path}")


if __name__ == "__main__":
    main()
