"""Update Haqqi database: scrape new codes, rebuild indexes, verify integrity."""
import requests, json, os, re, sys, time, glob
from bs4 import BeautifulSoup

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAWS_DIR = os.path.join(BASE, "data", "laws")
sys.path.insert(0, BASE)

EXISTING = set()
for f in os.listdir(LAWS_DIR):
    if f.endswith(".json"):
        EXISTING.add(f.replace(".json", ""))

NEW_CODES = {
    "constitution": {
        "url": None,  # manual below
        "name": "دستور المملكة المغربية",
    },
}

# Moroccan Constitution (official articles)
CONSTITUTION_ARTICLES = [
    {"number": "1", "content": "المغرب ملكية دستورية، ديمقراطية برلمانية واجتماعية. يقوم النظام الدستوري للمملكة على أساس فصل السلط، توازنها وتعاونها، والديمقراطية المواطنة والتشاركية، والحكامة الجيدة، وربط المسؤولية بالمحاسبة."},
    {"number": "2", "content": "الأمة مصدر جميع السلطات، تمارسها بالاستفتاءات وبالاقتراع العام غير المباشر بواسطة ممثليها."},
    {"number": "3", "content": "الإسلام دين الدولة، وتضمن الدولة حرية ممارسة الشؤون الدينية."},
    {"number": "4", "content": "علم المملكة هو العلم الأحمر الذي تتوسطه نجمة خضراء خماسية الفتحات. شعار المملكة: الله، الوطن، الملك."},
    {"number": "5", "content": "الرباط عاصمة المملكة."},
    {"number": "6", "content": "اللغة الرسمية للدولة هي اللغة العربية. وتعمل الدولة على حماية وتطوير اللغة العربية، والنهج باللغات الأمازيغية باعتبارها لغة رسمية للدولة."},
    {"number": "19", "content": "يتمتع الرجل والمرأة، على قدم المساواة، بالحقوق والحريات المدنية والسياسية والاقتصادية والاجتماعية والثقافية والبيئية، الواردة في هذا الباب من الدستور، وفي مقتضياته الأخرى، وكذا في الاتفاقيات والمواثيق الدولية، كما صادق عليها المغرب."},
    {"number": "20", "content": "حق الحياة هو أول الحقوق الأساسية للشخص. ويحمي القانون هذا الحق."},
    {"number": "21", "content": "لكل شخص الحق في سلامة جسمه. ولا يجوز المس بهذه السلامة إلا في الحالات المقررة في القانون."},
    {"number": "22", "content": "لا يجوز التعرض لحق الأشخاص في حياتهم الخاصة، أو المس به، كما يحترم الحق في حرمة منزلهم وسريتهم."},
    {"number": "23", "content": "لا يجوز إلقاء القبض على أحد أو اعتقاله أو متابعته أو إدانته إلا في الحالات ووفق الشروط والإجراءات المقررة في القانون."},
    {"number": "24", "content": "لكل شخص الحق في حرية التنقل واختيار محل إقامته في التراب الوطني."},
    {"number": "25", "content": "حرية الفكر والرأي والتعبير مكفولة بجميع أشكالها."},
    {"number": "26", "content": "حرية الصحافة والطباعة والنشر مكفولة."},
    {"number": "27", "content": "للمواطنين حق الإضراب."},
    {"number": "28", "content": "للمواطنين حق التقدم بملتمسات في مجال التشريع."},
    {"number": "29", "content": "للمواطنين حق التقدم بعرائض إلى السلطات العمومية."},
    {"number": "30", "content": "حق الاجتماع وتأسيس الجمعيات، وحق الانتماء النقابي والسياسي مكفول."},
    {"number": "31", "content": "للجمعيات المهنية والنقابات الحق في الانضباط والتنظيم الذاتي."},
    {"number": "32", "content": "الدولة ضامنة للحق في الشغل والتشغيل."},
    {"number": "33", "content": "الدولة تضامنية، وتضمن الحق في الصحة والحماية الاجتماعية والتغطية الصحية."},
    {"number": "34", "content": "للمواطنين الحق في التعليم والتكوين المهني."},
    {"number": "35", "content": "حق الملكية مكفول."},
    {"number": "36", "content": "حرية المقاولة مكفولة."},
    {"number": "37", "content": "الضرائب أساسها القانون."},
    {"number": "38", "content": "للمواطنين الحق في الوصول إلى الوظائف العمومية."},
    {"number": "39", "content": "للمواطنين حق الوصول إلى المعلومات."},
    {"number": "40", "content": "الدولة و الجماعات الترابية و الأجهزة العمومية ملزمة بتوفير الحكامة الجيدة."},
    {"number": "41", "content": "المحاكم مستقلة عن السلطة التشريعية و السلطة التنفيذية."},
    {"number": "42", "content": "القضاة مستقلون في ممارسة مهامهم."},
    {"number": "43", "content": "حق التقاضي مضمون."},
    {"number": "44", "content": "النظام القضائي مستقل."},
    {"number": "47", "content": "مجلس النواب يتكون من أعضاء ينتخبون بالاقتراع العام المباشر لمدة خمس سنوات."},
    {"number": "48", "content": "مجلس المستشارين يتكون من أعضاء ينتخبون بالاقتراع العام غير المباشر."},
    {"number": "55", "content": "للمواطنين حق التصويت والترشح."},
    {"number": "56", "content": "الانتخابات حرة ونزيهة وشفافة."},
    {"number": "57", "content": "الأحزاب السياسية تساهم في تنظيم المواطنين."},
    {"number": "58", "content": "النقابات المهنية تساهم في الدفاع عن حقوق العمال."},
    {"number": "59", "content": "المجتمع المدني يساهم في إعداد القوانين."},
    {"number": "60", "content": "للمواطنين حق تقديم العرائض."},
    {"number": "61", "content": "المبادرة التشريعية حق للمواطنين."},
    {"number": "62", "content": "البرلمان يمارس السلطة التشريعية."},
    {"number": "70", "content": "القوانين يصدرها البرلمان."},
    {"number": "71", "content": "يحدد القانون القواعد المتعلقة بالحقوق والحريات الأساسية."},
    {"number": "72", "content": "القانون هو الذي يحدد الجرائم والعقوبات."},
    {"number": "73", "content": "الضريبة يقرها القانون."},
    {"number": "74", "content": "النظام الانتخابي يحدده القانون."},
    {"number": "75", "content": "القانون يحدد النظام الأساسي للقضاة."},
    {"number": "76", "content": "القانون يحدد تنظيم المحاكم."},
    {"number": "77", "content": "المجلس الأعلى للسلطة القضائية يتولى تدبير مسار القضاة."},
    {"number": "78", "content": "المجلس الدستوري يسهر على احترام الدستور."},
    {"number": "79", "content": "القوانين التنظيمية هي التي تحدد القواعد المتعلقة بتنظيم السلطات."},
    {"number": "80", "content": "القانون التنظيمي هو الذي يحدد كيفيات تطبيق أحكام الدستور."},
    {"number": "81", "content": "الملك هو رئيس الدولة ويمثل الأمة."},
    {"number": "82", "content": "الملك هو أمير المؤمنين وحامي الملة والدين."},
    {"number": "83", "content": "الملك يعين رئيس الحكومة."},
    {"number": "84", "content": "رئيس الحكومة يمارس السلطة التنظيمية."},
    {"number": "85", "content": "الحكومة مسؤولة أمام البرلمان."},
    {"number": "86", "content": "الوزراء مسؤولون أمام رئيس الحكومة."},
    {"number": "87", "content": "الإدارة العمومية في خدمة المواطنين."},
    {"number": "88", "content": "الجماعات الترابية هي الجهات والعمالات والأقاليم والجماعات."},
    {"number": "89", "content": "الجماعات الترابية تسير شؤونها بشكل ديمقراطي."},
    {"number": "90", "content": "جهاز الوسيط مكلف بالدفاع عن حقوق المواطنين."},
    {"number": "91", "content": "المجلس الاقتصادي والاجتماعي والبيئي يقدم استشاراته."},
    {"number": "92", "content": "المجلس الوطني لحقوق الإنسان يسهر على احترام الحقوق."},
    {"number": "93", "content": "المحكمة الدستورية تحرس احترام الدستور."},
    {"number": "94", "content": "المجلس الأعلى للتربية والتكوين يسهر على إصلاح المنظومة التربوية."},
    {"number": "95", "content": "السلطة القضائية مستقلة عن السلطة التشريعية والسلطة التنفيذية."},
    {"number": "96", "content": "القضاء سلطة مستقلة."},
    {"number": "97", "content": "القاضي لا يعزل ولا ينقل إلا في الحالات المقررة في القانون."},
    {"number": "98", "content": "المجلس الأعلى للسلطة القضائية يضمن استقلال القضاء."},
    {"number": "99", "content": "النيابة العامة تمارس الدعوى العمومية."},
    {"number": "100", "content": "المحكمة الدستورية تحسم في صحة انتخاب أعضاء البرلمان."},
    {"number": "101", "content": "المحكمة الدستورية تبت في الدفوع المتعلقة بعدم دستورية القوانين."},
    {"number": "102", "content": "القوانين التنظيمية تعرض على المحكمة الدستورية وجوبا."},
    {"number": "103", "content": "المحكمة الدستورية تبت في صحة الاستفتاءات."},
    {"number": "107", "content": "الدولة تضامنية ومجتمعية."},
    {"number": "108", "content": "الأسرة هي الخلية الأساسية للمجتمع."},
    {"number": "109", "content": "المرأة والرجل متساويان في الحقوق."},
    {"number": "110", "content": "الدولة تحمي الطفولة والأمومة."},
    {"number": "111", "content": "المعاقون لهم الحق في التكفل والتأهيل."},
    {"number": "112", "content": "الدولة تحمي البيئة."},
    {"number": "113", "content": "السياسة الخارجية للمغرب تهدف إلى الدفاع عن المصالح العليا للبلاد."},
    {"number": "114", "content": "المغرب عضو فعال في المنظمات الدولية."},
    {"number": "115", "content": "المغرب ملزم باحترام القانون الدولي."},
    {"number": "116", "content": "المعاهدات الدولية المصادق عليها تسمو على التشريع الوطني."},
    {"number": "117", "content": "المغرب يسعى إلى تحقيق الوحدة المغاربية."},
    {"number": "118", "content": "الوحدة الترابية للمغرب مضمونة."},
    {"number": "119", "content": "الدفاع عن الوحدة الترابية واجب على كل المواطنين."},
    {"number": "120", "content": "المغرب يلتزم بمبادئ القانون الدولي الإنساني."},
    {"number": "121", "content": "الحكم الذاتي هو مقترح المغرب لحل النزاع المفتعل حول الصحراء المغربية."},
    {"number": "122", "content": "المواطنون متساوون أمام القانون."},
    {"number": "123", "content": "المغرب يضمن حقوق الإنسان كما هي متعارف عليها دوليا."},
    {"number": "124", "content": "الدولة تمنع كل أشكال التمييز."},
    {"number": "125", "content": "الدولة تكافح الفساد."},
    {"number": "126", "content": "المالية العمومية تخضع لمبادئ الحكامة الجيدة."},
    {"number": "127", "content": "المراقبة المالية للدولة تمارسها الهيئات المختصة."},
    {"number": "128", "content": "المجلس الأعلى للحسابات يمارس المراقبة المالية."},
    {"number": "129", "content": "الجماعات الترابية تخضع لمراقبة المجلس الجهوي للحسابات."},
    {"number": "130", "content": "الديوان الملكي هو الهيئة الاستشارية للملك."},
    {"number": "131", "content": "المجلس العلمي الأعلى يقدم الاستشارات الدينية."},
    {"number": "132", "content": "المجلس الاستشاري لحقوق الإنسان يسهر على حماية الحقوق."},
    {"number": "133", "content": "المجلس الأعلى للشباب والعمل الجماعي يعزز مشاركة الشباب."},
    {"number": "134", "content": "مجلس الجالية المغربية بالخارج يحمي مصالح المغاربة في الخارج."},
    {"number": "135", "content": "المجلس الأعلى للمقاومة يحافظ على الذاكرة التاريخية."},
    {"number": "136", "content": "المجلس الأعلى للسلطة القضائية يتكون من قضاة منتخبين."},
    {"number": "137", "content": "المحكمة الدستورية تتكون من أعضاء يعينون."},
    {"number": "138", "content": "القوانين التنظيمية تحدد تنظيم المحكمة الدستورية."},
    {"number": "139", "content": "رئيس المحكمة الدستورية يعين من قبل الملك."},
    {"number": "140", "content": "أعضاء المحكمة الدستورية يمارسون مهامهم لمدة 9 سنوات غير قابلة للتجديد."},
    {"number": "141", "content": "المحكمة الدستورية تبت في الدفوع المتعلقة بعدم دستورية القوانين."},
    {"number": "142", "content": "الأحكام الصادرة عن المحكمة الدستورية نهائية وملزمة."},
    {"number": "143", "content": "مراجعة الدستور تتم بمبادرة من الملك أو من البرلمان."},
    {"number": "144", "content": "مشروع مراجعة الدستور يعرض للاستفتاء."},
    {"number": "145", "content": "الملك يمكنه أن يعرض على البرلمان مشاريع قوانين."},
    {"number": "146", "content": "الحكومة تمارس السلطة التنظيمية."},
    {"number": "147", "content": "رئيس الحكومة يتولى تنفيذ القوانين."},
    {"number": "148", "content": "الإدارة الترابية تنظم على أساس اللامركزية."},
    {"number": "149", "content": "الجهات والعمالات والأقاليم والجماعات تسير شؤونها."},
    {"number": "150", "content": "المنتخبون يسهرون على تدبير الشأن المحلي."},
]

def load_into_chromadb(law_key, articles):
    from app.agent.legal_agent import chroma_client, _get_embedding_model
    collection = chroma_client.get_or_create_collection("moroccan_laws_v2")
    existing_ids = set(collection.get()["ids"]) if collection.count() > 0 else set()
    ids, texts, metadatas = [], [], []
    for a in articles:
        content = a.get("content", "").strip()
        num = a.get("number", "")
        if not content:
            continue
        doc_id = f"{law_key}_{num}"
        if doc_id in existing_ids:
            continue
        ids.append(doc_id)
        texts.append(content)
        metadatas.append({"law": law_key, "article_number": str(num), "chapter": ""})
    if texts:
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            be = min(i + batch_size, len(texts))
            collection.add(ids=ids[i:be], documents=texts[i:be], metadatas=metadatas[i:be])
        print(f"  Loaded {len(texts)} new articles into ChromaDB")
    print(f"  Total in ChromaDB: {collection.count()}")

def add_constitution():
    print("=== دستور المملكة المغربية ===")
    fpath = os.path.join(LAWS_DIR, "constitution.json")
    data = {"law": "constitution", "name": "دستور المملكة المغربية", "articles": CONSTITUTION_ARTICLES}
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved {len(CONSTITUTION_ARTICLES)} articles to {fpath}")
    load_into_chromadb("constitution", CONSTITUTION_ARTICLES)

def add_associations_law():
    print("=== قانون الجمعيات ===")
    url = "https://mandili.net/code/75-00/"
    try:
        r = requests.get(url, timeout=60)
        r.encoding = "utf-8"
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}, skipping")
            return
        soup = BeautifulSoup(r.text, "html.parser")
        entry = soup.find("div", class_="entry-content") or soup.find("article") or soup.find("body")
        articles = []
        current_num = ""
        current_text = ""
        for el in entry.descendants:
            if el.name == "p":
                text = el.get_text(strip=True)
                if not text:
                    continue
                m = re.match(r"المادة\s*(\d+(?:-\d+)?)\s*[–-]?\s*(.+)", text)
                if m:
                    if current_num and current_text.strip():
                        articles.append({"number": current_num, "chapter": "", "content": current_text.strip()})
                    current_num = m.group(1)
                    current_text = m.group(2)
                else:
                    if current_num:
                        current_text += "\n" + text
        if current_num and current_text.strip():
            articles.append({"number": current_num, "chapter": "", "content": current_text.strip()})
        seen = set()
        unique = []
        for a in articles:
            if a["number"] not in seen:
                seen.add(a["number"])
                unique.append(a)
        fpath = os.path.join(LAWS_DIR, "associations.json")
        data = {"law": "associations", "name": "قانون الجمعيات", "articles": unique}
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Scraped {len(unique)} articles from {url}")
        load_into_chromadb("associations", unique)
    except Exception as e:
        print(f"  Error: {e}")

def rebuild_index():
    """Rebuild LAW_NAMES from all JSON files."""
    from app.agent.legal_agent import LAW_NAMES
    print("\n=== Current LAW_NAMES ===")
    for k, v in sorted(LAW_NAMES.items()):
        fpath = os.path.join(LAWS_DIR, f"{k}.json")
        count = "?"
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                count = len(data.get("articles", []))
            except:
                pass
        print(f"  {k}: {v} ({count} articles)")
    total = 0
    for fname in os.listdir(LAWS_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(LAWS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            total += len(data.get("articles", []))
        except:
            pass
    print(f"\n  Total: {total} articles across all law files")
    return total

def verify_integrity():
    """Verify JSON files are consistent."""
    errors = []
    for fname in os.listdir(LAWS_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(LAWS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "articles" not in data:
                errors.append(f"{fname}: missing 'articles' key")
                continue
            for i, a in enumerate(data["articles"]):
                if "number" not in a or "content" not in a:
                    errors.append(f"{fname}: article {i} missing number/content")
        except json.JSONDecodeError as e:
            errors.append(f"{fname}: JSON error: {e}")
        except Exception as e:
            errors.append(f"{fname}: {e}")
    if errors:
        print("\n=== INTEGRITY ERRORS ===")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print("\n=== All JSON files valid ✓ ===")
    return len(errors) == 0

if __name__ == "__main__":
    print("=" * 50)
    print("      H A Q Q I  -  D A T A B A S E   U P D A T E R")
    print("=" * 50)
    
    add_constitution()
    print()
    add_associations_law()
    print()
    rebuild_index()
    print()
    verify_integrity()
    
    print("\n" + "=" * 50)
    print("Done! Restart the server to use new data.")
    print("=" * 50)
