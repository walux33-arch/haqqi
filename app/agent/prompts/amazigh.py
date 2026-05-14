"""أمازيغية (Tamazight) support for Haqi.

تنفيذ تدريجي لدعم اللغة الأمازيغية كلغة رسمية وفق الدستور المغربي (الفصل 5).
"""

# ⵜⵉⵣⵔⴰⵡⵉⵏ ⵜⵉⵡⵏⵏⴰⵙⵉⵏ ⴷ ⵜⵓⵜⵍⴰⵢⵜ ⵜⴰⵎⴰⵣⵉⵖⵜ
# القوانين الأساسية باللغة الأمازيغية

AMAZIGH_LAW_TERMS = {
    "ⴰⵣⵔⴼ": "حق (Droit)",
    "ⵜⵉⵣⵔⴰⵡⵉⵏ": "قوانين (Lois)",
    "ⴰⴱⵔⴽⴰⵏ": "محامي (Avocat)",
    "ⵜⴰⵏⵣⵣⴰⵔⵜ": "عدالة (Justice)",
    "ⴰⵙⵇⵇⵉⵎ ⵏ ⵓⵏⵥⴰⵔ": "محكمة (Tribunal)",
    "ⴰⵥⵓⵕ": "أصل / هوية (Identité)",
    "ⵜⴰⵎⴰⵡⴰⵙⵜ": "خدمة (Service)",
    "ⴰⵎⴰⴳⵔⴰⴷ": "مادة (Article)",
    "ⴰⵎⴰⵔⴰ": "مرسوم (Décret)",
    "ⴰⵏⴰⴼⵔⴰⵏ": "حماية (Protection)",
    "ⵜⵉⵎⴰⵜⴰⵔⵉⵏ ⵜⵉⵏⴼⵔⴰⵏⵉⵏ": "المعطيات الشخصية (Données personnelles)",
    "ⴰⵎⵓⵜⵜⵉ ⵏ ⵓⵏⴰⴼⵔⴰⵏ": "الأمن القانوني (Sécurité juridique)",
}

AMAZIGH_GREETING = "ⴰⵣⵓⵍ ⴰⵎⴰⵣⵉⵖ ⵙ ⵀⴰⵇⵇⵉ! ⵉⵙ ⵜⵔⵉⴷ ⴰⴷ ⵜⵙⵇⵙⴰⴷ ⵅⴼ ⵓⵣⵔⴼ ⴰⵎⵖⵔⵉⴱⵉ?"
# "مرحباً أمازيغياً بحقي! هل تريد أن تسأل عن القانون المغربي؟"

AMAZIGH_FALLBACK = "ⵙⵓⵔⵉ ⵜⵓⵜⵍⴰⵢⵜ ⵜⴰⵎⴰⵣⵉⵖⵜ ⴷⴰⵔⵉ ⵖⵉⵍⴰ ⵙ ⵜⴰⵡⵏⵏⴰⵙⵜ. ⵜⴰⵡⵏⵏⴰⵙⵜ ⵜⴰⵎⴰⵣⵉⵖⵜ ⵏⵏⴰⵖ ⵜⵍⵍⴰ ⴳ ⵓⵙⵙⴰⵔⵓ ⵏ ⵓⵏⴼⴰⵔⵏ. ⵉⵎⵎⴰ ⵜⵖⴰⵔⴰⵙⵜ ⵏ ⵓⵣⵔⴼ ⵜⵍⵍⴰ ⵙ ⵜⵓⵜⵍⴰⵢⵜ ⵜⴰⵄⵕⴰⴱⵜ ⵏⵖ ⵜⴰⴷⴰⵔⵉⵊⴰ."
# "معذرة، اللغة الأمازيغية عندي بشكل محدود. النسخة الأمازيغية كاينة فالتطوير. التحليل القانوني كاين بالعربية ولا الدارجة."


def is_amazigh(text: str) -> bool:
    """Detect if text contains Tifinagh characters."""
    tifinagh_range = range(0x2D30, 0x2D7F)
    for char in text:
        if ord(char) in tifinagh_range:
            return True
    return False


def get_amazigh_terms(arabic_term: str) -> str:
    """Translate Arabic legal terms to Amazigh (Tifinagh)."""
    for amz, arb in AMAZIGH_LAW_TERMS.items():
        if arabic_term in arb:
            return amz
    return arabic_term


def enhance_system_prompt(original_prompt: str) -> str:
    """Add Amazigh awareness to the system prompt."""
    return original_prompt + f"""

دعم اللغة الأمازيغية (Tamazight):
- إذا كان السؤال بالأمازيغية (حروف Tifinagh)، جاوب بالعربية/الدارجة وأضف الترجمة الأمازيغية للمصطلحات الرئيسية
- استعمل المصطلحات القانونية الأمازيغية: {', '.join(list(AMAZIGH_LAW_TERMS.keys())[:6])}
- الهدف هو تعزيز الطابع الرسمي للأمازيغية وفق الفصل 5 من الدستور"""
