"""Full ingestion pipeline: extract → anonymize → structure → index."""

import os
import json
import uuid
import time
import hashlib
from datetime import datetime
from typing import Optional

from app.ingestion.ocr import extract_text
from app.ingestion.anonymizer import anonymize_text, detect_pii
from app.ingestion.structurer import structure_document
from app.ingestion.models import (
    IngestedDocument, DocumentSource, DocumentType, IngestionStatus
)
from app.agent.legal_agent import agent, groq_client, chroma_client


INGESTION_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ingested")
os.makedirs(INGESTION_DIR, exist_ok=True)

INDEX_PATH = os.path.join(INGESTION_DIR, "index.json")


def _load_index() -> dict:
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {"documents": [], "total": 0}


def _save_index(index: dict):
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


class IngestionPipeline:
    def __init__(self):
        self._groq_classifier = groq_client is not None

    def ingest_file(self, filepath: str, title: str = "", source: DocumentSource = DocumentSource.UPLOAD) -> IngestedDocument:
        """Full pipeline for a single file."""
        doc_id = uuid.uuid4().hex[:12]
        doc = IngestedDocument(
            id=doc_id,
            title=title or os.path.splitext(os.path.basename(filepath))[0],
            source=source,
            status=IngestionStatus.PENDING,
        )

        try:
            # 1. Extract
            doc.status = IngestionStatus.EXTRACTING
            raw_text = extract_text(filepath)
            if not raw_text:
                doc.status = IngestionStatus.FAILED
                doc.error = "لم يتم استخراج أي نص من الملف"
                self._record(doc)
                return doc
            doc.content = raw_text

            # 2. Anonymize
            doc.status = IngestionStatus.ANONYMIZING
            pii_count = detect_pii(raw_text)
            doc.metadata["pii_detected"] = pii_count
            clean_text = anonymize_text(raw_text, level="standard")
            doc.content = clean_text

            # 3. Structure
            doc.status = IngestionStatus.STRUCTURING
            meta = structure_document(clean_text, title=title)
            doc.chamber = meta["chamber"]
            doc.court = meta["court"]
            doc.law_domain = meta["law_domain"]
            doc.year = meta["year"]
            doc.doc_type = DocumentType(meta["doc_type"])
            doc.tags = [t for t in [meta["law_domain"], meta["chamber"]] if t]

            # Groq-based classification for richer tagging (optional)
            if self._groq_classifier and len(clean_text) > 50:
                try:
                    groq_tags = self._classify_with_groq(clean_text[:1500], title)
                    for tag in groq_tags:
                        if tag and tag not in doc.tags:
                            doc.tags.append(tag)
                    doc.metadata["groq_classification"] = groq_tags
                except Exception as e:
                    print(f"Groq classification error: {e}")

            # 4. Index into ChromaDB
            doc.status = IngestionStatus.INDEXING
            self._index_to_chromadb(doc)

            doc.status = IngestionStatus.COMPLETED
        except Exception as e:
            doc.status = IngestionStatus.FAILED
            doc.error = str(e)

        self._record(doc)
        return doc

    def ingest_url(self, url: str, title: str = "") -> IngestedDocument:
        """Import document from URL (scrape content)."""
        import urllib.request
        import tempfile

        doc_id = uuid.uuid4().hex[:12]
        doc = IngestedDocument(
            id=doc_id,
            title=title or url,
            source=DocumentSource.URL,
            source_url=url,
            status=IngestionStatus.PENDING,
        )

        try:
            doc.status = IngestionStatus.EXTRACTING
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; HaqiTechBot/1.0; +https://haqqi.ma)"
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            # Simple HTML-to-text extraction
            import re
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                doc.status = IngestionStatus.FAILED
                doc.error = "لم يتم استخراج نص من الرابط"
                self._record(doc)
                return doc
            doc.content = text

            doc.status = IngestionStatus.ANONYMIZING
            pii_count = detect_pii(text)
            doc.metadata["pii_detected"] = pii_count
            doc.content = anonymize_text(text, level="standard")

            doc.status = IngestionStatus.STRUCTURING
            meta = structure_document(doc.content, title=title, url=url)
            doc.chamber = meta["chamber"]
            doc.court = meta["court"]
            doc.law_domain = meta["law_domain"]
            doc.year = meta["year"]
            doc.doc_type = DocumentType(meta["doc_type"])
            doc.tags = [t for t in [meta["law_domain"], meta["chamber"]] if t]

            if self._groq_classifier and len(doc.content) > 50:
                try:
                    groq_tags = self._classify_with_groq(doc.content[:1500], title)
                    for tag in groq_tags:
                        if tag and tag not in doc.tags:
                            doc.tags.append(tag)
                except Exception:
                    pass

            doc.status = IngestionStatus.INDEXING
            self._index_to_chromadb(doc)

            doc.status = IngestionStatus.COMPLETED
        except Exception as e:
            doc.status = IngestionStatus.FAILED
            doc.error = str(e)

        self._record(doc)
        return doc

    def ingest_text(self, text: str, title: str = "", doc_type: str = "other") -> IngestedDocument:
        """Direct text ingestion (for pasted content)."""
        doc_id = uuid.uuid4().hex[:12]
        doc = IngestedDocument(
            id=doc_id,
            title=title or f"نص مستورد {doc_id}",
            source=DocumentSource.MANUAL,
            status=IngestionStatus.PENDING,
        )

        try:
            doc.status = IngestionStatus.ANONYMIZING
            doc.content = anonymize_text(text, level="standard")

            doc.status = IngestionStatus.STRUCTURING
            meta = structure_document(doc.content, title=title)
            doc.chamber = meta["chamber"]
            doc.court = meta["court"]
            doc.law_domain = meta["law_domain"]
            doc.year = meta["year"]
            doc.doc_type = DocumentType(meta["doc_type"])
            doc.tags = [t for t in [meta["law_domain"], meta["chamber"]] if t]

            doc.status = IngestionStatus.INDEXING
            self._index_to_chromadb(doc)

            doc.status = IngestionStatus.COMPLETED
        except Exception as e:
            doc.status = IngestionStatus.FAILED
            doc.error = str(e)

        self._record(doc)
        return doc

    def _classify_with_groq(self, text: str, title: str) -> list[str]:
        """Use Groq to extract legal tags from document content."""
        if not groq_client:
            return []
        prompt = f"""استخرج من النص القانوني التالي 3-5 كلمات مفتاحية (tags) بالعربية تصف المجال القانوني والمحكمة والموضوع.
أرجع فقط الكلمات المفتاحية مفصولة بفواصل، بدون شرح.

العنوان: {title}
النص: {text[:1500]}"""
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=100,
        )
        tags_text = response.choices[0].message.content
        return [t.strip() for t in tags_text.split(",") if t.strip()]

    def _index_to_chromadb(self, doc: IngestedDocument):
        """Add document to ChromaDB for semantic search."""
        try:
            collection = chroma_client.get_or_create_collection("moroccan_laws")
            content_hash = hashlib.md5(doc.content.encode()).hexdigest()
            existing = collection.get(ids=[content_hash])
            if existing and existing["ids"]:
                return  # Already indexed

            from app.agent.legal_agent import _get_embedding_model
            model = _get_embedding_model()
            embedding = model.encode(doc.content[:500]).tolist() if model else None

            collection.add(
                ids=[content_hash],
                embeddings=[embedding] if embedding else None,
                documents=[doc.content[:2000]],
                metadatas=[{
                    "law": "ingested",
                    "article_number": "",
                    "chapter": doc.law_domain,
                    "source": doc.source.value,
                    "title": doc.title,
                    "doc_type": doc.doc_type.value,
                    "court": doc.court,
                    "chamber": doc.chamber,
                    "year": doc.year or 0,
                    "tags": ",".join(doc.tags),
                    "ingested_at": doc.created_at,
                }],
            )
        except Exception as e:
            print(f"ChromaDB indexing error: {e}")
            raise

    def _record(self, doc: IngestedDocument):
        """Save document to local index."""
        index = _load_index()
        index["documents"].append(doc.to_dict())
        index["total"] = len(index["documents"])
        _save_index(index)

    def get_history(self, limit: int = 20) -> list:
        index = _load_index()
        docs = index["documents"]
        docs.sort(key=lambda d: d.get("created_at", ""), reverse=True)
        return docs[:limit]

    def get_stats(self) -> dict:
        index = _load_index()
        docs = index["documents"]
        completed = sum(1 for d in docs if d["status"] == "completed")
        failed = sum(1 for d in docs if d["status"] == "failed")
        by_type = {}
        for d in docs:
            t = d.get("doc_type", "other")
            by_type[t] = by_type.get(t, 0) + 1
        return {
            "total": index["total"],
            "completed": completed,
            "failed": failed,
            "by_type": by_type,
        }
