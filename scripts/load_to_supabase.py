"""Load law articles into Supabase with embeddings (laws / articles / embeddings tables)."""

import os
import json
import sys
from datetime import date
from dotenv import load_dotenv
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
model = SentenceTransformer("all-MiniLM-L6-v2")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "laws")

LAW_META = {
    "penal": {"title": "القانون الجنائي", "category": "penal", "source_url": "https://mandili.net/morocco/codes/penal-code/"},
    "doc": {"title": "قانون الالتزامات والعقود", "category": "civil", "source_url": "https://mandili.net/morocco/codes/obligations-and-contracts/"},
    "commercial": {"title": "القانون التجاري", "category": "commercial", "source_url": "https://mandili.net/morocco/codes/commercial-code/"},
    "family": {"title": "مدونة الأسرة", "category": "family", "source_url": "https://mandili.net/morocco/codes/family-code/"},
    "labour": {"title": "مدونة الشغل", "category": "labour", "source_url": "https://mandili.net/morocco/codes/labour-code/"},
}


def main():
    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith(".json"):
            continue
        law_key = fname.replace(".json", "")
        meta = LAW_META.get(law_key)
        if not meta:
            print(f"Skipping unknown file: {fname}")
            continue

        fpath = os.path.join(DATA_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        articles = data.get("articles", [])
        print(f"\n=== {meta['title']} ({law_key}) — {len(articles)} articles ===")

        # Insert or get existing law row
        existing = supabase.table("laws").select("id").eq("title", meta["title"]).execute()
        if existing.data:
            law_id = existing.data[0]["id"]
            print(f"  Law already exists, ID: {law_id}")
        else:
            law_row = {
                "title": meta["title"],
                "category": meta["category"],
                "source_url": meta["source_url"],
            }
            res = supabase.table("laws").insert(law_row).execute()
            law_id = res.data[0]["id"]
            print(f"  Created law ID: {law_id}")

        # Delete old articles + embeddings for this law
        old = supabase.table("articles").select("id").eq("law_id", law_id).execute()
        old_ids = [o["id"] for o in old.data]
        if old_ids:
            supabase.table("embeddings").delete().in_("source_id", old_ids).eq("source_table", "articles").execute()
            supabase.table("articles").delete().eq("law_id", law_id).execute()

        # Insert articles + embeddings in batches
        batch_size = 50
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            texts = [a["content"] for a in batch]

            # Insert articles
            article_rows = [
                {"law_id": law_id, "article_number": a["number"], "content": a["content"], "chapter": a.get("chapter", ""), "section": a.get("section", "")}
                for a in batch
            ]
            res = supabase.table("articles").insert(article_rows).execute()
            article_ids = [r["id"] for r in res.data]

            # Generate embeddings
            embeddings = model.encode(texts).tolist()

            # Insert embeddings
            emb_rows = [
                {"source_table": "articles", "source_id": article_ids[j], "content": texts[j], "embedding": embeddings[j], "metadata": {"law": law_key, "article_number": batch[j]["number"]}}
                for j in range(len(batch))
            ]
            supabase.table("embeddings").insert(emb_rows).execute()
            print(f"  Batch {i//batch_size + 1}: {len(batch)} articles + embeddings inserted")

    print("\nDone!")


if __name__ == "__main__":
    main()