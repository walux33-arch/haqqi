from enum import Enum
from datetime import datetime
from typing import Optional


class DocumentType(str, Enum):
    LAW = "law"
    JUDGEMENT = "judgement"
    CIRCULAR = "circular"
    CONTRACT = "contract"
    ADMINISTRATIVE = "administrative"
    OTHER = "other"


class DocumentSource(str, Enum):
    UPLOAD = "upload"
    URL = "url"
    SCRAPE = "scrape"
    API = "api"
    MANUAL = "manual"


class IngestionStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    ANONYMIZING = "anonymizing"
    STRUCTURING = "structuring"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestedDocument:
    def __init__(
        self,
        id: str,
        title: str,
        content: str = "",
        doc_type: DocumentType = DocumentType.OTHER,
        source: DocumentSource = DocumentSource.UPLOAD,
        source_url: str = "",
        chamber: str = "",
        court: str = "",
        year: Optional[int] = None,
        law_domain: str = "",
        tags: list[str] = None,
        metadata: dict = None,
        status: IngestionStatus = IngestionStatus.PENDING,
        error: str = "",
        created_at: str = "",
    ):
        self.id = id
        self.title = title
        self.content = content
        self.doc_type = doc_type
        self.source = source
        self.source_url = source_url
        self.chamber = chamber
        self.court = court
        self.year = year
        self.law_domain = law_domain
        self.tags = tags or []
        self.metadata = metadata or {}
        self.status = status
        self.error = error
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content_preview": self.content[:200] if self.content else "",
            "doc_type": self.doc_type,
            "source": self.source,
            "source_url": self.source_url,
            "chamber": self.chamber,
            "court": self.court,
            "year": self.year,
            "law_domain": self.law_domain,
            "tags": self.tags,
            "metadata": self.metadata,
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at,
        }
