"""PDF contract generation for Moroccan legal contracts."""

import os
import io
import json
from datetime import datetime

# Try fitz (PyMuPDF), fallback to reportlab
try:
    import fitz  # PyMuPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "contracts")

# Contract templates in Arabic
CONTRACT_TEMPLATES = {
    "rent": {
        "title": "عقد إيجار",
        "description": "كراء العقارات السكنية والتجارية",
        "fields": [
            {"name": "landlord", "label": "المُؤَجِّر (اسم الكامل)", "type": "text"},
            {"name": "tenant", "label": "المُسْتَأْجِر (الاسم الكامل)", "type": "text"},
            {"name": "property", "label": "وصف العقار", "type": "text"},
            {"name": "address", "label": "عنوان العقار", "type": "text"},
            {"name": "duration", "label": "مدة الإيجار", "type": "text", "default": "سنة واحدة"},
            {"name": "rent_amount", "label": "قيمة الكراء الشهرية (درهم)", "type": "number"},
            {"name": "start_date", "label": "تاريخ بداية العقد", "type": "date"},
            {"name": "city", "label": "المدينة", "type": "text", "default": "الدار البيضاء"},
        ],
    },
    "employment": {
        "title": "عقد عمل",
        "description": "عقد الشغل المحدد المدة",
        "fields": [
            {"name": "employer", "label": "المُشَغِّل (الاسم الكامل)", "type": "text"},
            {"name": "employee", "label": "الأَجِير (الاسم الكامل)", "type": "text"},
            {"name": "position", "label": "المنصب", "type": "text"},
            {"name": "salary", "label": "الأجر الشهري (درهم)", "type": "number"},
            {"name": "duration", "label": "مدة العقد", "type": "text", "default": "سنة واحدة"},
            {"name": "start_date", "label": "تاريخ بداية الشغل", "type": "date"},
            {"name": "workplace", "label": "مكان العمل", "type": "text"},
        ],
    },
    "partnership": {
        "title": "اتفاقية شراكة",
        "description": "عقد الشراكة بين الأطراف",
        "fields": [
            {"name": "partner1", "label": "الشريك الأول", "type": "text"},
            {"name": "partner2", "label": "الشريك الثاني", "type": "text"},
            {"name": "objective", "label": "غرض الشراكة", "type": "text"},
            {"name": "capital", "label": "رأس المال (درهم)", "type": "number"},
            {"name": "share1", "label": "نسبة الشريك الأول (%)", "type": "number"},
            {"name": "share2", "label": "نسبة الشريك الثاني (%)", "type": "number"},
            {"name": "city", "label": "المدينة", "type": "text", "default": "الدار البيضاء"},
            {"name": "date", "label": "تاريخ الاتفاقية", "type": "date"},
        ],
    },
}


def generate_pdf(contract_type: str, data: dict) -> bytes:
    if contract_type not in CONTRACT_TEMPLATES:
        raise ValueError(f"Unknown contract type: {contract_type}")

    if not HAS_PDF:
        return _generate_text_fallback(contract_type, data)

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Fonts
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    title_font = fitz.Font(fontfile=font_path) if os.path.exists(font_path) else None

    y = 50
    def write(text, size=12, bold=False, color=(0, 0, 0)):
        nonlocal y
        p = fitz.Point(50, y)
        font = title_font
        page.insert_text(p, text, fontname="helv" if not font else "helv", fontsize=size, color=color)
        y += size * 1.8

    # Title
    template = CONTRACT_TEMPLATES[contract_type]
    write(template["title"], size=20, color=(0.08, 0.30, 0.12))
    write("─" * 60, size=10, color=(0.5, 0.5, 0.5))

    # Content
    today = datetime.now().strftime("%d/%m/%Y")
    city = data.get("city", "الدار البيضاء")

    if contract_type == "rent":
        write(f"تحرر هذا العقد في {city} بتاريخ {data.get('start_date', today)}", size=11)
        write("")
        write("بين كل من:", size=12, bold=True)
        write(f"1. السيد(ة) {data.get('landlord', '__________')} يُسمى المؤجر، طرف أول.", size=11)
        write(f"2. السيد(ة) {data.get('tenant', '__________')} يُسمى المستأجر، طرف ثان.", size=11)
        write("")
        write("تم الاتفاق على ما يلي:", size=12, bold=True)
        write(f"المادة 1: أجرى المؤجر للمستأجر العقار الكائن بـ {data.get('address', '__________')} والمسمى {data.get('property', '__________')}.", size=11)
        write(f"المادة 2: مدة الإيجار {data.get('duration', 'سنة واحدة')} تبدأ من {data.get('start_date', today)}.", size=11)
        write(f"المادة 3: قيمة الكراء الشهرية {data.get('rent_amount', '______')} درهم.", size=11)
        write("المادة 4: يؤدي المستأجر وديعة تأمين تساوي شهر واحد.", size=11)
        write("المادة 5: يلتزم المستأجر باستعمال العقار استعمالا قانونيا.", size=11)
        write("المادة 6: يتحمل المؤجر مصاريف الترميمات الكبرى.", size=11)
        write("المادة 7: ينتهي العقد بانتهاء مدته، مع إمكانية التجديد باتفاق الطرفين.", size=11)
        write("")
        write("حرر في نسختين.", size=11)
        write("")
        write(f"توقيع المؤجر: ___________     توقيع المستأجر: ___________", size=11)

    elif contract_type == "employment":
        write(f"تحرر هذا العقد في {city} بتاريخ {data.get('start_date', today)}", size=11)
        write("")
        write("بين كل من:", size=12, bold=True)
        write(f"1. السيد(ة) {data.get('employer', '__________')} يُسمى المشغل، طرف أول.", size=11)
        write(f"2. السيد(ة) {data.get('employee', '__________')} يُسمى الأجير، طرف ثان.", size=11)
        write("")
        write("تم الاتفاق على ما يلي:", size=12, bold=True)
        write(f"المادة 1: يشغل الأجير لدى المشغل منصب {data.get('position', '__________')}.", size=11)
        write(f"المادة 2: مدة العقد {data.get('duration', 'سنة واحدة')} تبدأ من {data.get('start_date', today)}.", size=11)
        write(f"المادة 3: مكان العمل {data.get('workplace', '__________')}.", size=11)
        write(f"المادة 4: الأجر الشهري {data.get('salary', '______')} درهم.", size=11)
        write("المادة 5: مدة التجربة شهر واحد.", size=11)
        write("المادة 6: يستفيد الأجير من الحقوق المخولة قانونا.", size=11)
        write("المادة 7: يخضع العقد لمقتضيات مدونة الشغل.", size=11)
        write("")
        write("حرر في نسختين.", size=11)

    elif contract_type == "partnership":
        write(f"تحرر هذه الاتفاقية في {city} بتاريخ {data.get('date', today)}", size=11)
        write("")
        write("بين كل من:", size=12, bold=True)
        write(f"1. السيد(ة) {data.get('partner1', '__________')} شريك أول.", size=11)
        write(f"2. السيد(ة) {data.get('partner2', '__________')} شريك ثان.", size=11)
        write("")
        write("تم الاتفاق على ما يلي:", size=12, bold=True)
        write(f"المادة 1: تأسيس شراكة بين الطرفين غرضها {data.get('objective', '__________')}.", size=11)
        write(f"المادة 2: رأس مال الشراكة {data.get('capital', '______')} درهم.", size=11)
        write(f"المادة 3: حصة الشريك الأول {data.get('share1', '50')}% وحصة الشريك الثاني {data.get('share2', '50')}%.", size=11)
        write("المادة 4: توزع الأرباح والخسائر بنفس النسب.", size=11)
        write("المادة 5: تسير الشراكة باتفاق الطرفين.", size=11)
        write("المادة 6: تحل النزاعات وديا أو أمام المحاكم المختصة.", size=11)
        write("")
        write("حرر في نسختين.", size=11)

    write("")
    write("─" * 60, size=10, color=(0.5, 0.5, 0.5))
    write("هذا العقد أُنشئ بواسطة منصة حقي للمساعدة القانونية. لا يشكل استشارة قانونية.", size=9, color=(0.5, 0.5, 0.5))

    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    buf.seek(0)
    return buf.read()


def _generate_text_fallback(contract_type: str, data: dict) -> bytes:
    template = CONTRACT_TEMPLATES[contract_type]
    today = datetime.now().strftime("%d/%m/%Y")
    lines = [
        f"{'='*60}",
        f"  {template['title']}",
        f"{'='*60}",
        f"",
        f"تحرر هذا العقد في {data.get('city', 'الدار البيضاء')} بتاريخ {data.get('start_date') or data.get('date') or today}",
        f"",
    ]
    lines += ["بين:", ""]
    if contract_type == "rent":
        lines += [
            f"- المؤجر: {data.get('landlord', '__________')}",
            f"- المستأجر: {data.get('tenant', '__________')}",
            "",
            "تم الاتفاق على ما يلي:",
            f"1. العقار: {data.get('property', '__________')} ب {data.get('address', '__________')}",
            f"2. المدة: {data.get('duration', 'سنة واحدة')} من {data.get('start_date', today)}",
            f"3. الكراء: {data.get('rent_amount', '______')} درهم شهريا",
            "4. وديعة تأمين: شهر واحد",
            "5. يستعمل العقار استعمالا قانونيا",
        ]
    elif contract_type == "employment":
        lines += [
            f"- المشغل: {data.get('employer', '__________')}",
            f"- الأجير: {data.get('employee', '__________')}",
            "",
            "تم الاتفاق على ما يلي:",
            f"1. المنصب: {data.get('position', '__________')}",
            f"2. المدة: {data.get('duration', 'سنة واحدة')} من {data.get('start_date', today)}",
            f"3. مكان العمل: {data.get('workplace', '__________')}",
            f"4. الأجر: {data.get('salary', '______')} درهم شهريا",
            "5. مدة التجربة: شهر واحد",
        ]
    elif contract_type == "partnership":
        lines += [
            f"- الشريك الأول: {data.get('partner1', '__________')}",
            f"- الشريك الثاني: {data.get('partner2', '__________')}",
            "",
            "تم الاتفاق على ما يلي:",
            f"1. الغرض: {data.get('objective', '__________')}",
            f"2. رأس المال: {data.get('capital', '______')} درهم",
            f"3. النسب: {data.get('share1', '50')}% / {data.get('share2', '50')}%",
        ]
    lines += [
        "",
        f"حرر في {city} في نسختين.",
        "",
        "التوقيع 1: ___________     التوقيع 2: ___________",
        "",
        f"{'='*60}",
        "هذا العقد أُنشئ بواسطة منصة حقي. لا يشكل استشارة قانونية.",
    ]
    text = "\n".join(lines)
    return text.encode("utf-8")


def get_contract_templates():
    return {k: {"title": v["title"], "description": v["description"], "fields": v["fields"]}
            for k, v in CONTRACT_TEMPLATES.items()}
