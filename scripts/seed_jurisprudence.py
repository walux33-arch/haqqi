"""Index jurisprudence decisions into ChromaDB."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.agent.legal_agent import chroma_client

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "judgements")
fpath = os.path.join(DATA_DIR, "juricaf_decisions.json")

with open(fpath, "r", encoding="utf-8") as f:
    data = json.load(f)

collection = chroma_client.get_or_create_collection("moroccan_laws")
existing = set(collection.get()["ids"]) if collection.count() > 0 else set()

ids, texts, metadatas = [], [], []
for i, d in enumerate(data):
    desc = d.get("description", "").strip()
    title = d.get("title", "").strip()
    if not desc:
        continue
    content = f"{title}\n{desc}"
    doc_id = f"jurisprudence_{i}"
    if doc_id in existing:
        continue
    ids.append(doc_id)
    texts.append(content)
    metadatas.append({
        "law": "jurisprudence",
        "article_number": str(i + 1),
        "chapter": "",
        "title": title,
        "link": d.get("link", ""),
        "date": d.get("date", ""),
    })

if texts:
    print(f"Indexing {len(texts)} jurisprudence decisions into ChromaDB...")
    batch_size = 50
    for i in range(0, len(texts), batch_size):
        be = min(i + batch_size, len(texts))
        collection.add(ids=ids[i:be], documents=texts[i:be], metadatas=metadatas[i:be])
        print(f"  {be}/{len(texts)}")
    print(f"Done! Total in ChromaDB: {collection.count()}")
else:
    print(f"All {len(data)} decisions already indexed. Total: {collection.count()}")
