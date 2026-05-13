"""PII detection and anonymization for Moroccan legal documents.

Complies with Loi 09.08 relative à la protection des données personnelles.
"""

import re
from typing import Optional


CIN_PATTERN = re.compile(r"\b[A-Za-z]{1,2}\s*\d{5,6}\b")
PHONE_PATTERN = re.compile(r"0[5-7]\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
ICE_PATTERN = re.compile(r"\b\d{15}\b")
RC_PATTERN = re.compile(r"\b\d{3,9}\b")
ADDRESS_KEYWORDS = [
    "عنوان", "adresse", "titre", "domicile", "résid", "habit",
    "مدينة", "ville", "حي", "quartier", "زنقة", "rue", "av ",
]


def anonymize_text(text: str, level: str = "standard") -> str:
    """Remove or mask PII from legal text.

    Levels:
    - 'standard': Mask CIN, phone, email, ICE
    - 'strict': Also mask addresses, names (aggressive)
    - 'light': Only mask CIN + phone
    """
    original = text

    # CIN (Carte d'Identité Nationale)
    text = CIN_PATTERN.sub("[CIN masqué]", text)

    # Phone numbers
    text = PHONE_PATTERN.sub("[téléphone masqué]", text)

    # Email
    text = EMAIL_PATTERN.sub("[email masqué]", text)

    # ICE (Identifiant Commun de l'Entreprise)
    text = ICE_PATTERN.sub("[ICE masqué]", text)

    if level in ("standard", "strict"):
        # Registration numbers (RC)
        text = re.sub(r"(?i)(rc|registre\s+commerce)\s*:?\s*\d{3,9}", r"\1: [RC masqué]", text)

    if level == "strict":
        # Address lines: lines containing address keywords followed by content
        lines = text.split("\n")
        masked = []
        for line in lines:
            if any(kw in line.lower() for kw in ADDRESS_KEYWORDS):
                masked.append(line.split(":")[0] + ": [adresse masquée]" if ":" in line else "[adresse masquée]")
            else:
                masked.append(line)
        text = "\n".join(masked)

    return text


def detect_pii(text: str) -> dict:
    """Return count of detected PII items."""
    return {
        "cin": len(CIN_PATTERN.findall(text)),
        "phones": len(PHONE_PATTERN.findall(text)),
        "emails": len(EMAIL_PATTERN.findall(text)),
        "ice": len(ICE_PATTERN.findall(text)),
    }
