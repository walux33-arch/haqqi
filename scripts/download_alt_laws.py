"""Download Moroccan law texts from alternative sources"""
import os, json, re, httpx, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "laws")
BASE = "https://adala.justice.gov.ma"

# The laws are accessible via the web interface
# Let's check the folder page which should list files
FOLDER_IDS = {
    "penal": 21,
    "doc": 22,
    "commercial": 829,
    "family": 26,
    "labour": 20,
}

def get_folder_files(folder_id):
    """Try to get files from a folder via the API or web"""
    # Try different API patterns
    patterns = [
        f"/api/folders/{folder_id}",
    ]
    for p in patterns:
        r = httpx.get(BASE + p, follow_redirects=True, timeout=15)
        if r.status_code == 200:
            try:
                return r.json()
            except:
                pass
    return None

def try_download_pdf(url, name):
    """Try to download a PDF"""
    try:
        r = httpx.get(url, follow_redirects=True, timeout=30)
        if r.status_code == 200 and "pdf" in r.headers.get("content-type", ""):
            path = os.path.join(os.path.dirname(DATA_DIR), "pdfs", f"{name}.pdf")
            with open(path, "wb") as f:
                f.write(r.content)
            return len(r.content)
    except:
        pass
    return 0

print("Checking adala.ma for law files...")

# Check if we can find PDF URLs
for law_name, fid in FOLDER_IDS.items():
    data = get_folder_files(fid)
    if data:
        print(f"{law_name} (fid={fid}): {json.dumps(data, ensure_ascii=False)[:200]}")

# Try getting the main laws page for list of laws
r = httpx.get(BASE + "/folders/12", follow_redirects=True, timeout=15)
print(f"\nFolders page: {r.status_code}, len={len(r.text)}")

# Extract any PDF links
pdf_links = re.findall(r'(/api/uploads/[^"\'\s]+\.pdf)', r.text)
print(f"\nPDF links found: {len(pdf_links)}")
for link in pdf_links[:5]:
    print(f"  {link[:100]}...")

print("\nDone. Data sources need to be verified manually.")
