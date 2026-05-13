"""Legal qualification engine: domain classifier, norm hierarchy, anti-abrogation.

Implémente la "Qualification Juridique Automatisée" — le cœur de l'architecture Haqi.
"""

import re
from typing import Optional

# ─── Domaines juridiques (Legal Domains) ───

DOMAINS = {
    "الأسرة": {
        "keywords": ["زواج", "طلاق", "نفقة", "حضانة", "ولاية", "إرث", "وصية", "ميراث",
                     "خطوبة", "صداق", "طليقة", "مطلق", "متزوج", "تطليق", "خلع",
                     "الطلاق", "الزواج", "الأسرة", "مدونة الأسرة"],
        "laws": ["family"],
        "description": "مدونة الأسرة - الأحوال الشخصية",
    },
    "التجاري": {
        "keywords": ["تجارة", "تاجر", "شركة", "محل تجاري", "سجل تجاري", "أعمال تجارية",
                     "SARL", "SA", "تأسيس شركة", "مسؤولية تجارية", "إفلاس", "تسوية",
                     "كراء تجاري", "محل صناعي", "محل حرفي", "القانون 49.16",
                     "الشيك", "الكمبيالة", "السفتجة", "الأوراق التجارية"],
        "laws": ["commercial"],
        "description": "القانون التجاري",
    },
    "الالتزامات والعقود": {
        "keywords": ["عقد", "التزام", "اتفاق", "إيجاب", "قبول", "مسؤولية", "تعويض",
                     "ضرر", "خطأ", "تعهد", "شروط", "بطلان", "فسخ", "انفساخ",
                     "قوة قاهرة", "ظرف طارئ", "الالتزامات", "العقود", "ظهير",
                     "D.O.C", "ظهيرة الالتزامات"],
        "laws": ["doc"],
        "description": "ظهيرة الالتزامات والعقود",
    },
    "الجنائي": {
        "keywords": ["جريمة", "جنحة", "جناية", "مخالفة", "عقوبة", "سجن", "حبس",
                     "غرامة", "مسؤولية جنائية", "محكمة جنائية", "قانون جنائي",
                     "سرقة", "نصب", "اختلاس", "ضرب", "جرح", "قتل", "تزوير",
                     "الرشوة", "تبديد", "خيانة أمانة"],
        "laws": ["penal"],
        "description": "القانون الجنائي",
    },
    "الشغل": {
        "keywords": ["شغل", "عمل", "أجير", "أجراء", "مأجور", "مقاول", "تشغيل",
                     "عقد شغل", "عقد عمل", "فصل", "تسريح", "إقالة", "استقالة",
                     "أجر", "راتب", "تعويض عن المدة", "إجازة", "رخصة",
                     "محكمة اجتماعية", "مجلس الأعلى"],
        "laws": ["labour"],
        "description": "مدونة الشغل",
    },
    "الجمركي والجبائي": {
        "keywords": ["ضريبة", "جبا", "TVA", "T.P", "I.R", "I.S", "الضريبة",
                     "تصريح", "أداء", "رسوم", "حقوق", "المدونة العامة للضرائب",
                     "CGI", "تعريفة", "جمركة", "استيراد", "تصدير",
                     "منازعة ضريبية", "طعن ضريبي", "المادة 165"],
        "laws": ["tax", "commercial"],
        "description": "المدونة العامة للضرائب",
    },
    "العقاري": {
        "keywords": ["عقار", "عقاري", "ملك", "ملكية", "أرض", "بناء", "عقار محفظ",
                     "التحفيظ العقاري", "الرهن", "الرسم العقاري", "المحافظة العقارية",
                     "كراء", "إيجار", "سكني", "مكري", "مكتري", "عدة الكراء",
                     "الحقوق العينية", "مدونة الحقوق العينية", "حق عيني", "عينية"],
        "laws": ["real_property"],
        "description": "مدونة الحقوق العينية",
    },
    "الإداري": {
        "keywords": ["إداري", "إدارية", "جماعة", "ترابي", "محكمة إدارية",
                     "قرار إداري", "صفقة عمومية", "طلب", "رخصة", "ترخيص",
                     "مرفق عام", "مواطن", "إدارة", "تبسيط المساطر",
                     "القانون 55.19", "الرشادة", "الحكامة"],
        "laws": ["admin"],
        "description": "القانون الإداري",
    },
    "الاستهلاك": {
        "keywords": ["مستهلك", "استهلاك", "شراء", "بيع", "منتج", "خدمة",
                     "ضمان", "إرجاع", "ثمن", "فاتورة", "حماية المستهلك",
                     "قانون المستهلك", "التجارة الإلكترونية"],
        "laws": ["consumer_protection"],
        "description": "قانون حماية المستهلك",
    },
    "التأمينات": {
        "keywords": ["تأمين", "تأمينات", "شركة تأمين", "بوليصة", "عقد تأمين",
                     "تعويض", "حادثة", "مسؤولية مدنية", "سيارة", "عربة",
                     "ضمان", "مدونة التأمينات"],
        "laws": ["insurance_code"],
        "description": "مدونة التأمينات",
    },
    "الجمعيات": {
        "keywords": ["جمعية", "جمعيات", "تأسيس جمعية", "قانون الجمعيات",
                     "منظمة غير حكومية", "تسجيل", "إعلان",
                     "قانون 06.07", "القانون 15.18"],
        "laws": ["associations"],
        "description": "قانون الجمعيات",
    },
    "الدستوري": {
        "keywords": ["دستور", "دستوري", "حقوق", "حريات", "حكم", "محكمة دستورية",
                     "المجلس الدستوري", "الفصل", "مبدأ", "مساواة", "مواطنة",
                     "القضاء الدستوري", "العدالة الدستورية"],
        "laws": ["constitution"],
        "description": "الدستور المغربي",
    },
    "المساطر": {
        "keywords": ["مسطرة", "إجراء", "تبليغ", "تنفيذ", "حكم", "أمر", "مقرر",
                     "استئناف", "نقض", "طعن", "أجل", "ميعاد", "اختصاص",
                     "مسطرة جنائية", "مسطرة مدنية", "المسطرة"],
        "laws": ["criminal_procedure", "doc"],
        "description": "قانون المسطرة",
    },
}

# ─── تدرج النصوص القانونية (Norm Hierarchy) ───

NORM_HIERARCHY = {
    1: "الدستور",
    2: "القوانين التنظيمية (Lois Organiques)",
    3: "المعاهدات والاتفاقيات الدولية",
    4: "القوانين العادية (Lois Ordinaires)",
    5: "المراسيم (Décrets)",
    6: "القرارات التنظيمية (Arrêtés)",
    7: "المناشير والدوريات (Circulaires)",
    8: "الاجتهاد القضائي (Jurisprudence)",
}

LAW_PRIORITY = {
    "constitution": 1,
    "organic_law": 2,
    "family": 4,
    "commercial": 4,
    "penal": 4,
    "labour": 4,
    "consumer_protection": 4,
    "insurance_code": 4,
    "criminal_procedure": 4,
    "doc": 4,
    "real_property": 4,
    "associations": 4,
    "tax": 4,
    "ingested": 7,
    "jurisprudence": 8,
}

# ─── قوانين ملغاة أو منسوخة (Abrogated/Modified Laws) ───

ABROGATED_LAWS = {
    "قانون 06.07": {
        "status": "منسوخ",
        "replaced_by": "القانون 15.18",
        "replaced_date": "2018",
        "note": "قانون الجمعيات القديم، حل محله القانون 15.18",
    },
    "ظهير 24.05.1958": {
        "status": "منسوخ جزئياً",
        "replaced_by": "القانون 55.19",
        "replaced_date": "2019",
        "note": "تبسيط المساطر الإدارية",
    },
}

# ─── مصطلحات قانونية (Legal Terminology) ───

LEGAL_TERMS = {
    "الدفع بعدم القبول": "Fin de non-recevoir",
    "بطلان العقد": "Nullité du contrat",
    "القوة الملزمة": "Force obligatoire",
    "التبليغ القانوني": "Notification légale",
    "التكييف القانوني": "Qualification juridique",
    "الأمن القانوني": "Sécurité juridique",
    "المسؤولية التقصيرية": "Responsabilité délictuelle",
    "المسؤولية التعاقدية": "Responsabilité contractuelle",
    "حالة القوة القاهرة": "Cas de force majeure",
    "الظرف الطارئ": "Théorie de l'imprévision",
    "الحيازة": "Possession",
    "التقادم": "Prescription",
    "الإثراء بلا سبب": "Enrichissement sans cause",
}


class LegalQualification:
    """Legal qualification engine — identifies domain, hierarchy, abrogation."""

    def qualify(self, question: str) -> dict:
        """Full qualification of a legal question."""
        q_lower = question.lower()
        scores = {}

        for domain, config in DOMAINS.items():
            score = sum(2 if kw in q_lower else 0 for kw in config["keywords"])
            if score > 0:
                scores[domain] = score

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        primary_domain = ranked[0][0] if ranked else "عام"
        primary_laws = DOMAINS.get(primary_domain, {}).get("laws", [])

        # Determine norm hierarchy priority
        max_priority = 8
        for law in primary_laws:
            p = LAW_PRIORITY.get(law, 8)
            if p < max_priority:
                max_priority = p

        return {
            "primary_domain": primary_domain,
            "domains": [d for d, _ in ranked[:3]],
            "relevant_laws": primary_laws,
            "norm_level": max_priority,
            "norm_label": NORM_HIERARCHY.get(max_priority, "غير محدد"),
            "description": DOMAINS.get(primary_domain, {}).get("description", ""),
        }

    def check_abrogation(self, law_name: str) -> Optional[dict]:
        """Check if a law has been abrogated or modified."""
        for key, info in ABROGATED_LAWS.items():
            if key in law_name or law_name in key:
                return info
        return None

    def get_norm_label(self, law_key: str) -> str:
        """Get the norm hierarchy label for a law."""
        priority = LAW_PRIORITY.get(law_key, 8)
        return NORM_HIERARCHY.get(priority, "غير محدد")

    def search_terms(self, text: str) -> list[dict]:
        """Find legal terms in text with French translations."""
        found = []
        for term_ar, term_fr in LEGAL_TERMS.items():
            if term_ar in text:
                found.append({"arabic": term_ar, "french": term_fr})
        return found


qualifier = LegalQualification()
