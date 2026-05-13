"""Metadata extraction, tagging, and classification of legal documents."""

import re
from typing import Optional

from app.ingestion.models import DocumentType

# ─── Chamber detection (French → Arabic mapping) ───
CHAMBER_KEYWORDS = {
    "commerciale": ["تجاري", "تجارية", "شركة", "شركات", "تجار", "محل تجاري", "commercial"],
    "sociale": ["اجتماعي", "شغل", "عمل", "أجير", "أجراء", "مأجور", "social"],
    "civile": ["مدني", "مسؤولية", "تعويض", "ضرر", "civil"],
    "criminelle": ["جنائي", "جنحة", "جناية", "عقوبة", "سجن", "penal"],
    "familiale": ["أسرة", "زواج", "طلاق", "نفقة", "حضانة", "ولاية", "family"],
    "administrative": ["إداري", "إدارية", "جماعة", "ترابي", "صفقة", "administrative"],
    "immobilière": ["عقار", "عقاري", "ملك", "أرض", "بناء", "immobilier"],
    "fiscale": ["ضريبة", "جبائي", "ضريبي", "TVA", "impôt", "fiscal"],
}

# ─── Court level detection ───
COURT_PATTERNS = {
    "محكمة النقض": r"(?i)(محكمة\s+النقض|cour\s+de\s+cassation)",
    "محكمة الاستئناف": r"(?i)(محكمة\s+الاستئناف|cour\s+d['']appel)",
    "المحكمة الابتدائية": r"(?i)(محكمة\s+ابتدائية|tribunal\s+de\s+première\s+instance)",
    "المحكمة الإدارية": r"(?i)(محكمة\s+إدارية|tribunal\s+administratif)",
    "المحكمة التجارية": r"(?i)(محكمة\s+تجارية|tribunal\s+de\s+commerce)",
}

# ─── Law domain detection ───
DOMAIN_KEYWORDS = {
    "التجاري": ["تجاري", "تجارية", "شركة", "شركات", "تاجر", "محل تجاري", "السجل التجاري", "commercial"],
    "الأسرة": ["أسرة", "زواج", "طلاق", "نفقة", "حضانة", "ولاية", "إرث", "وصية"],
    "الجنائي": ["جنائي", "جنحة", "جناية", "عقوبة", "سجن", "حبس", "غرامة"],
    "الشغل": ["شغل", "عمل", "أجير", "أجراء", "مأجور", "تشغيل", "مقاول"],
    "العقاري": ["عقار", "عقاري", "ملك", "أرض", "بناء", "رهن", "كراء"],
    "الإداري": ["إداري", "إدارية", "جماعة", "ترابي", "صفقة"],
    "الضريبي": ["ضريبة", "جبائي", "ضريبي", "TVA", "impôt"],
    "الالتزامات": ["التزام", "عقد", "مسؤولية", "تعويض", "ضرر", "مدني"],
    "الدستوري": ["دستور", "دستوري", "حقوق", "حريات"],
}

YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")

DECISION_NUMBER_PATTERN = re.compile(r"(?:قرار|arrêt|décision)\s*(?:عدد|n[°o]?)?\s*(\d+)", re.IGNORECASE)


def detect_chamber(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for chamber, keywords in CHAMBER_KEYWORDS.items():
        score = sum(2 if kw in text_lower else 0 for kw in keywords)
        if score > 0:
            scores[chamber] = score
    if scores:
        return max(scores, key=scores.get)
    return ""


def detect_court(text: str) -> str:
    for court_name, pattern in COURT_PATTERNS.items():
        if re.search(pattern, text):
            return court_name
    return ""


def detect_domain(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(2 if kw in text_lower else 0 for kw in keywords)
        if score > 0:
            scores[domain] = score
    if scores:
        return max(scores, key=scores.get)
    return ""


def detect_year(text: str) -> Optional[int]:
    years = YEAR_PATTERN.findall(text)
    if years:
        return int(years[0])
    return None


def detect_decision_number(text: str) -> str:
    m = DECISION_NUMBER_PATTERN.search(text)
    return m.group(1) if m else ""


def classify_document_type(text: str, title: str = "") -> DocumentType:
    combined = (title + " " + text).lower()

    if any(kw in combined for kw in ["قرار", "arrêt", "jugement", "حكم", "محكمة", "cour"]):
        if any(kw in combined for kw in ["تعليمة", "منشور", "circulaire", "note"]):
            return DocumentType.CIRCULAR
        return DocumentType.JUDGEMENT

    if any(kw in combined for kw in ["ظهير", "قانون", "loi", "مرسوم", "décret", "المادة"]):
        return DocumentType.LAW

    if any(kw in combined for kw in ["منشور", "مذكرة", "circulaire", "note ministérielle", "مديرية"]):
        return DocumentType.CIRCULAR

    if any(kw in combined for kw in ["اتفاقية", "contract", "عقد", "اتفاق"]):
        return DocumentType.CONTRACT

    if any(kw in combined for kw in ["إداري", "جماعة", "إدارية", "صفقة عمومية", "marché public"]):
        return DocumentType.ADMINISTRATIVE

    return DocumentType.OTHER


def structure_document(text: str, title: str = "", url: str = "") -> dict:
    """Extract all metadata from a document text."""
    return {
        "chamber": detect_chamber(text),
        "court": detect_court(text),
        "law_domain": detect_domain(text),
        "year": detect_year(text),
        "decision_number": detect_decision_number(text),
        "doc_type": classify_document_type(text, title).value,
    }
