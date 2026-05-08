"""Explore jurisprudence sources for Moroccan legal data.

Checked sources:
- adala.justice.gov.ma - laws PDFs
- juricaf.org - Cour de cassation decisions via RSS (3,172 decisions)
- data.gov.ma - open data portal
"""

import httpx


def check_juricaf():
    url = "https://juricaf.org/recherche/+/facet_pays:Maroc?format=rss"
    r = httpx.get(url, follow_redirects=True, timeout=30)
    print(f"juricaf.org: status={r.status_code}, size={len(r.content)} bytes")

    import xml.etree.ElementTree as ET
    root = ET.fromstring(r.content)
    items = list(root.iter("item"))
    print(f"  Items in feed: {len(items)}")

    total_tag = root.find(".//{http://a9.com/-/spec/opensearch/1.1/}totalResults")
    if total_tag is not None:
        print(f"  Total results: {total_tag.text}")

    for link in root.iter("link"):
        rel = link.get("rel", "")
        if rel in ("next", "last"):
            print(f"  Pagination: rel={rel}, href={link.get('href', '')}")


def main():
    print("=== juricaf.org ===")
    check_juricaf()

    print("\n=== adala.justice.gov.ma ===")
    for folder_id in [19, 21, 22, 23, 57]:
        url = f"https://adala.justice.gov.ma/api/folders/12/{folder_id}"
        r = httpx.get(url, timeout=30)
        print(f"  Folder {folder_id}: status={r.status_code}", end="")
        if r.status_code == 200:
            data = r.json()
            files = data.get("files", data.get("data", []))
            print(f", files={len(files) if files else 0}")
        else:
            print()


if __name__ == "__main__":
    main()
