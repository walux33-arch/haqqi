"""Seed ChromaDB - optimized for CPU."""
import os, json, time
import chromadb

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
LAWS_DIR = os.path.join(PROJECT_DIR, "data", "laws")
CHROMA_DIR = os.path.join(PROJECT_DIR, "chroma_db")

LAW_NAMES = {
    "penal": "القانون الجنائي",
    "doc": "ظهيرة الالتزامات والعقود",
    "commercial": "القانون التجاري",
    "family": "مدونة الأسرة",
    "labour": "مدونة الشغل",
}

def load_articles():
    articles = []
    for fname in sorted(os.listdir(LAWS_DIR)):
        if not fname.endswith(".json"):
            continue
        law_key = fname.replace(".json", "")
        fpath = os.path.join(LAWS_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for art in data.get("articles", []):
            content = art.get("content", "").strip()
            if content:
                articles.append({
                    "law": law_key,
                    "article_number": str(art.get("number", "")),
                    "content": content,
                })
    return articles

def main():
    t0 = time.time()
    print("Loading embedding model (paraphrase-multilingual-MiniLM-L12-v2)...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
    print(f"Model loaded in {time.time()-t0:.1f}s")

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    for old_name in ["moroccan_laws", "moroccan_laws_v2"]:
        try:
            client.delete_collection(old_name)
        except Exception:
            pass
    collection = client.create_collection("moroccan_laws_v2")

    articles = load_articles()
    print(f"Loaded {len(articles)} articles (no chunking)")

    BATCH = 32
    total = len(articles)
    for start in range(0, total, BATCH):
        end = min(start + BATCH, total)
        batch = articles[start:end]
        texts = [d["content"] for d in batch]
        ids = [f"{d['law']}_art{d['article_number']}" for d in batch]
        metadatas = [{"law": d["law"], "article_number": d["article_number"]} for d in batch]

        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        collection.add(embeddings=embeddings, documents=texts, metadatas=metadatas, ids=ids)

        elapsed = time.time() - t0
        pct = 100 * end // total
        rate = end / elapsed if elapsed > 0 else 0
        eta = (total - end) / rate if rate > 0 else 0
        print(f"  {end}/{total} ({pct}%) | {rate:.1f} docs/s | ETA: {eta:.0f}s")

    print(f"\nDone! {collection.count()} documents in ChromaDB")
    print(f"Total time: {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
