"""Load law articles from JSON files into ChromaDB"""
import os, json, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agent.legal_agent import chroma_client, LegalAgent

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "laws")
agent = LegalAgent()

def main():
    collection = chroma_client.get_or_create_collection("moroccan_laws")

    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith(".json"):
            continue
        law_name = fname.replace(".json", "")
        fpath = os.path.join(DATA_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        articles = data.get("articles", [])
        if not articles:
            print(f"{law_name}: 0 articles, skip")
            continue

        ids = []
        texts = []
        metadatas = []
        for art in articles:
            content = art.get("content", "").strip()
            num = art.get("number", "")
            if not content:
                continue
            ids.append(f"{law_name}_{num}")
            texts.append(content)
            metadatas.append({
                "law": law_name,
                "article_number": num,
                "chapter": "",
            })

        if texts:
            collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
            )
            print(f"{law_name}: loaded {len(texts)} articles")

    print(f"\nTotal in ChromaDB: {collection.count()}")

    # Test search
    print("\n=== Test: البحث عن عقود الإيجار ===")
    results = agent._search_all("عقود الإيجار في القانون المغربي")
    for r in results[:3]:
        print(f"  [{r['law']} - مادة {r['article']}]: {r['content'][:80]}...")


if __name__ == "__main__":
    main()
