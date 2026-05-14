"""Module تبسيط المساطر الإدارية - Loi 55.19.

يساعد المواطنين على فهم المساطر الإدارية وتبسيطها وفق مقتضيات القانون 55.19
والمنصة الرقمية "الرشادة" (Rachad).
"""

import re
from app.agent.modules import register

# ─── المساطر الإدارية المدعومة ───

ADMIN_PROCEDURES = {
    "بطاقة التعريف الوطنية": {
        "keywords": ["بطاقة", "تعريف", "CIN", "بطاقة وطنية"],
        "service": "الوكالة الوطنية لتقنين الأنشطة",
        "documents": ["نسخة من عقد الازدياد", "صور فوتوغرافية", "الرسوم (30 درهم)"],
        "delay": "24 ساعة",
        "online": True,
        "url": "https://www.cnie.ma",
        "loi": "المرسوم رقم 2.20.389",
    },
    "جواز السفر": {
        "keywords": ["جواز", "سفر", "passport", "پاسپور"],
        "service": "السلطات المحلية",
        "documents": ["بطاقة التعريف الوطنية", "صور فوتوغرافية", "الرسوم (300 درهم)"],
        "delay": "5 أيام",
        "online": True,
        "url": "https://www.passeport.ma",
        "loi": "المرسوم رقم 2.19.825",
    },
    "رخصة السياقة": {
        "keywords": ["رخصة", "سياقة", "permis", "قيادة"],
        "service": "الوكالة الوطنية للسلامة الطرقية (NARSA)",
        "documents": ["بطاقة التعريف", "شهادة طبية", "صور فوتوغرافية"],
        "delay": "15 يوم",
        "online": True,
        "url": "https://www.narsa.ma",
        "loi": "القانون 52.05",
    },
    "السجل التجاري": {
        "keywords": ["سجل تجاري", "تسجيل تجاري", "RC", "registre commerce"],
        "service": "المحكمة التجارية / كتابة الضبط",
        "documents": ["عقد التأسيس", "نسخة من بطاقة التعريف", "شهادة الإيداع القانوني"],
        "delay": "3 أيام",
        "online": True,
        "url": "https://www.rc.ma",
        "loi": "القانون 15.95",
    },
    "شهادة السكنى": {
        "keywords": ["شهادة", "سكنى", "سكن", " domicile"],
        "service": "الملحقة الإدارية / المنطقة",
        "documents": ["عقد الكراء أو عقد الملكية", "فواتير الماء والكهرباء", "بطاقة التعريف"],
        "delay": "24 ساعة",
        "online": False,
        "url": "",
        "loi": "المرسوم رقم 2.20.389",
    },
    "تصحيح الحالة المدنية": {
        "keywords": ["حالة مدنية", "تصحيح", "رسم الولادة", "عقد ازدياد", "زواج"],
        "service": "المحكمة الابتدائية / قسم الحالة المدنية",
        "documents": ["نسخة من عقد الازدياد", "شهادة من المستشفى", "بطاقة التعريف", "مقرر قضائي"],
        "delay": "30 يوماً",
        "online": False,
        "url": "",
        "loi": "القانون 37.99",
    },
    "التسجيل في المبادرة الوطنية للتنمية البشرية (INDH)": {
        "keywords": ["مبادرة", "INDH", "تنمية", "دعم", "تمويل"],
        "service": "عمالة / إقليم",
        "documents": ["ملف المشروع", "بطاقة التعريف", "شهادة السكنى"],
        "delay": "30 يوماً",
        "online": False,
        "url": "",
        "loi": "المبادرة الوطنية للتنمية البشرية",
    },
    "طلب رخصة البناء": {
        "keywords": ["بناء", "رخصة بناء", "permis", "تعمير", "عقار"],
        "service": "الجماعة الترابية / قسم التعمير",
        "documents": ["مخطط الهندسة", "شهادة الملكية", "رخصة التجزئة العقارية"],
        "delay": "30 يوماً",
        "online": True,
        "url": "https://www.roc.ma",
        "loi": "القانون 12.90",
    },
}

# ─── نصوص القانون 55.19 ───

LOI_55_19_ARTICLES = [
    ("المادة 1", "يهدف هذا القانون إلى تبسيط المساطر والإجراءات الإدارية وتقليص آجالها وتجويد الخدمات العمومية."),
    ("المادة 2", "تطبق مقتضيات هذا القانون على جميع الإدارات العمومية والجماعات الترابية والمؤسسات العمومية."),
    ("المادة 3", "تلتزم الإدارات بنشر قائمة المساطر والإجراءات الإدارية على منصة 'الرشادة' الإلكترونية."),
    ("المادة 4", "تحدد آجال معالجة ملفات المرتفقين بما لا يتجاوز 30 يوماً ما لم ينص قانون خاص على خلاف ذلك."),
    ("المادة 5", "يحق للمرتفق متابعة حالة ملفه إلكترونياً عبر منصة 'الرشادة'."),
    ("المادة 6", "تحدث آلية للتبليغ الإلكتروني للمقررات الإدارية."),
    ("المادة 7", "تلغى جميع المقتضيات المخالفة للقانون 55.19."),
]


def match(question: str) -> bool:
    q = question.lower()
    keywords = [
        "مسطرة", "إدار", "رشادة", "55.19", "إجراء", "إدارية",
        "معاملة", "ملف", "وثيقة", "شهادة", "طلب", "رخصة",
        "بطاقة", "جواز", "سفر", "سجل", "تجاري", "بناء",
        "الوكالة", "المبادرة", "INDH", "administratif",
    ]
    return any(kw in q for kw in keywords)


def process(question: str, context: str = "") -> str:
    """Analyze the question and return administrative simplification info."""
    q = question.lower()

    # Find matching procedure
    matched_procedure = None
    matched_score = 0
    for name, proc in ADMIN_PROCEDURES.items():
        score = sum(2 if kw in q else 0 for kw in proc["keywords"])
        if score > matched_score:
            matched_score = score
            matched_procedure = (name, proc)

    result_parts = []

    if matched_procedure and matched_score >= 2:
        name, proc = matched_procedure
        result_parts.append(f"**{name}**")
        result_parts.append(f"الخدمة: {proc['service']}")
        result_parts.append(f"الوثائق المطلوبة:\n" + "\n".join(f"- {d}" for d in proc["documents"]))
        result_parts.append(f"آجال المعالجة: {proc['delay']}")
        result_parts.append(f"الإطار القانوني: {proc['loi']}")
        if proc["online"] and proc["url"]:
            result_parts.append(f"✅ يمكن تقديم الطلب إلكترونياً عبر: {proc['url']}")
        else:
            result_parts.append("⚠️ هذه المسطرة تتطلب الحضور شخصياً إلى مصلحة الإدارة المعنية.")

        result_parts.append(f"\n---\nوفق مقتضيات القانون 55.19 المتعلق بتبسيط المساطر والإجراءات الإدارية، يمكنك متابعة حالة ملفك عبر منصة 'الرشادة' (Rachad).")
    else:
        # General Loi 55.19 guidance
        result_parts.append("وفق القانون 55.19 المتعلق بتبسيط المساطر والإجراءات الإدارية:")
        for article, content in LOI_55_19_ARTICLES[:4]:
            result_parts.append(f"📌 **{article}**: {content}")
        result_parts.append("\nيمكنك الاطلاع على جميع المساطر الإدارية عبر منصة 'الرشادة': https://rachad.ma")
        result_parts.append("أو الاتصال بالخط المباشر للتبليغ عن التعقيدات الإدارية: 5757")

    result_parts.append("\n*هاد معلومات عامة للاسترشاد وفق القانون 55.19. راجع الإدارة المعنية للحصول على التفاصيل الدقيقة.*")
    return "\n\n".join(result_parts)


# Register module
register(type("AdminSimplificationModule", (), {
    "name": "admin_simplification",
    "label": "تبسيط المساطر الإدارية (Loi 55.19)",
    "description": "مساعدة المواطنين في المساطر الإدارية وفق القانون 55.19 ومنصة الرشادة",
    "match": staticmethod(match),
    "process": staticmethod(process),
}))
