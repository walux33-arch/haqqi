import os
import json
import hashlib
import time
import threading
from functools import lru_cache
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client
from app.data_gov import fetch_gov_stats

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
) if GROQ_API_KEY else None

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

chroma_client = chromadb.PersistentClient(
    path=os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
)

LAW_NAMES = {
    "penal": "القانون الجنائي",
    "doc": "ظهيرة الالتزامات والعقود",
    "commercial": "القانون التجاري",
    "family": "مدونة الأسرة",
    "labour": "مدونة الشغل",
    "criminal_procedure": "قانون المسطرة الجنائية",
    "consumer_protection": "قانون حماية المستهلك",
    "real_property": "مدونة الحقوق العينية",
    "insurance_code": "مدونة التأمينات",
    "constitution": "دستور المملكة المغربية",
    "associations": "قانون الجمعيات",
}

# Simple answer cache (LRU: 64 entries)
_answer_cache = {}


DARIJA_PROMPT_SHORT = """نت حقي (Haqi)، العقل الرقمي لشركة HaqiTech. مساعد قانوني مغربي بالدارجة، خبير فالقانون المغربي والهندسة المقاولاتية والجبائية وتحليل الاجتهاد القضائي.

القواعد الأساسية (ممنوع المخالفة):
1. إذا كان السؤال قانوني: استعمل ONLY المعلومات القانونية لي كيجيوك فـ "المعلومات القانونية" تحت. ذكر دائما رقم المادة واسم القانون. ما تعطيش جواب عام بلا مصادر.
2. ما تحاولش تجاوب من عندك — المعلومات القانونية المقدمة ليك هي مصدرك الوحيد. إذا ما كانتش كافية، قل "هاد المعلومات ناقصة، راجع محامي مختص".
3. جاوب بالتفصيل (بين 6 و 12 جملة)، شرح وافي ومتكامل
4. جاوب بالدارجة المغربية
5. فالنهاية، قل "هاد معلومات عامة للاسترشاد، راجع محامي باش تأكد"
6. تنوع فالأجوبة — ما تعاودش نفس الصياغة فكل مرة""""

CAPABILITIES_DESC = """أنا حقي (Haqi)، العقل الرقمي لشركة HaqiTech. كايخدم النظام ديالي على 4 ركائز أساسية:

1. الاستيعاب الشامل والتحيين الآني (L'Ingestion et l'Indexation):
   - كنفهرس جميع الوثائق المنشورة في الجريدة الرسمية و بوابة "عدالة" (Adala.ma)
   - هضمت 5,757+ مادة من 11 مدونة قانونية + الدستور المغربي: ظهير الالتزامات والعقود، مدونة التجارة، القانون الجنائي، مدونة الأسرة، مدونة الشغل، قانون المسطرة الجنائية، قانون حماية المستهلك، مدونة الحقوق العينية، مدونة التأمينات، قانون الجمعيات، الدستور، والمدونة العامة للضرائب (CGI)
   - التحيين فوري: بمجرد ما كيخرج قانون جديد، السيستم كيدير تحيين باش ما نعطيش معلومات قديمة

2. هندسة التكييف القانوني (Qualification Juridique Automatisée):
   - ملي كتعطيني نازلة، الخوارزميات كدير "التكييف القانوني السليم"
   - مثال: إذا كان السؤال على نزاع فكراء محل تجاري، كنمشي لـ القانون رقم 49.16 ونفهم واش حنا بصدد إفراغ ولا تعويض ولا تجديد عقد
   - كنخدم بمنطق "القياس والاستنباط" اللي كيخدم به القاضي والمحامي

3. تحليل الاجتهاد القضائي (Analyse de la Jurisprudence):
   - ملقم بآلاف قرارات محكمة النقض (Cour de Cassation) — التجارية، المدنية، الاجتماعية، الجنائية
   - ما كنكتفيش بالنص القانوني الجامد، كنقول كيفاش فسراتو المحكمة وشنو هو التوجه القضائي
   - كنضمن "الأمن القانوني" (Sécurité Juridique) بالتوجيه ديال القضاء المستقر
   - كنجيب القرارات المطابقة للموضوع ديالك باش تفهم كيفاش المحكمة كتطبق القانون فالحالات المشابهة

4. محرك الاستدلال المرجعي (RAG - Retrieval-Augmented Generation):
   - ما كنخترعش الأجوبة (No Hallucinations)
   - Query: تحط السؤال → Search: نقلب فقاعدة البيانات الموثقة → Retrieval: نجبد النص القانوني الأصلي → Generation: نصيغ الجواب بالدارجة مع المصطلحات التقنية بالفصحى

التخصصات القطاعية (Modules Spécialisés):
- الطبقة المحاسبية: فهم المخطط المحاسبي المغربي (PCM) و Audit المالي للجمعيات والشركات
- الطبقة الضريبية: خبير فمساطر المنازعات الضريبية وأجال الطعون (المادة 165 CGI)
- طبقة القانون الإداري: الحكامة الجيدة والديمقراطية التشاركية (القانون التنظيمي 113.14)
- الهندسة المقاولاتية: تأسيس SARL AU، التحكيم الضريبي، انتزاع منح ميثاق الاستثمار 03.22، Leasing"""


DEMO_ANSWERS = {
    "زواج": "شروط الزواج فالمغرب منظمة فمدونة الأسرة. المادة 14 كاتقول بلي الزواج requires الإذن من القاضي إذا كان أحد الطرفين menor. المادة 10 كاتحدد سن الزواج فـ 18 سنة.",
    "طلاق": "الطلاق فالمغرب منظم فمدونة الأسرة. المادة 70 كاتقول بلي الطلق إما يكون باتفاق الزوجين (طلاق الاتفاق) أو بقرار من القاضي (طلاق التطليق). المادة 78 كاتحدد حالات التطليق.",
    "عمل": "مدونة الشغل فالمغرب كاتنظم العلاقات الشغلية. المادة 20 كاتقول بلي العقد الشغل خاص يكون فالكتابة. المادة 36 كاتحدد المدة القصوى للعمل فـ 10 ساعات فاليوم و 44 ساعة فالأسبوع.",
    "كراء": "كراء العقارات فالمغرب منظم فظهيرة الالتزامات والعقود. المادة 620 كاتقول بلي عقد الكراء خاص يكون فالكتابة. المادة 625 كاتحدد حقوق وواجبات المكري والمكتري.",
    "شركة": "تأسيس الشركة فالمغرب كايحتاج لـ: 1) عقد التأسيس devant notaire، 2) الإيداع فالمحكمة التجارية، 3) النشر فالجريدة الرسمية. المادة 5 من القانون التجاري كاتحدد أنواع الشركات.",
    "إرث": "الإرث فالمغرب منظم فمدونة الأسرة. المادة 218 كاتحدد أصحاب الفروض ونصيب كل واحد. المادة 225 كاتقول بلي الزوجة ترث ربع تركة زوجها إذا ما كانتش عندو ولاد.",
}

DEMO_FALLBACK = "مرحبا بك في حقي! أنا مساعدك القانوني المغربي. كنقدر نعاونك فلمواضيع التالية:\n• الزواج والطلاق (مدونة الأسرة)\n• العقود والالتزامات\n• القانون التجاري وتأسيس الشركات\n• القانون الجنائي\n• قانون الشغل\n\nعفوا، هادي نسخة تجريبية. باش تحصل على جواب كامل، خاصك تحط GROQ_API_KEY فـ .env"


_embedding_model = None
_embedding_lock = threading.Lock()
_embedding_event = threading.Event()

def _load_embedding_model():
    global _embedding_model
    with _embedding_lock:
        if _embedding_model is not None:
            _embedding_event.set()
            return _embedding_model
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        with _embedding_lock:
            _embedding_model = model
    except Exception as e:
        print(f"Embedding model load error: {e}")
    _embedding_event.set()
    return _embedding_model

def _get_embedding_model():
    if _embedding_model is not None:
        return _embedding_model
    _embedding_event.wait(timeout=120)
    return _embedding_model

# Start loading in background
import threading
threading.Thread(target=_load_embedding_model, daemon=True).start()


class LegalAgent:
    def __init__(self):
        self._collection = None

    @property
    def is_demo(self):
        return groq_client is None or GROQ_API_KEY is None or GROQ_API_KEY == "your_groq_api_key_here"

    def _generate_embedding(self, text: str):
        model = _get_embedding_model()
        if model is None:
            return None
        return model.encode(text).tolist()

    def _get_collection(self):
        if self._collection is None:
            self._collection = chroma_client.get_or_create_collection("moroccan_laws")
        return self._collection

    def _cache_key(self, question: str) -> str:
        return hashlib.md5(question.encode()).hexdigest()

    def _is_about_self(self, question: str) -> bool:
        q = question.lower()
        keywords = ["حقي", "haqqi", "haqi", "كيفاش كايخدم", "كيفاش كتخدم", "شنو هي قدراتك",
                     "واش كتقدر", "شنو كتعرف", "كيفاش كتشتغل", "واش كتسالي", "كيفاش يمكنك",
                     "what can you do", "how do you work", "tell me about yourself",
                     "من تكون", "شنو هو حقي", "الخدمات", "capabilities"]
        for kw in keywords:
            if kw in q:
                return True
        return False

    def query(self, question: str, context=None, history=None):
        if context:
            return self._ask_groq(question, context, history)
        if self._is_about_self(question):
            return self._ask_groq(question, CAPABILITIES_DESC, history)
        ck = self._cache_key(question)
        if history is None and ck in _answer_cache:
            return _answer_cache[ck]
        results = self._search_all(question)
        answer = self._ask_groq(question, results, history)
        if history is None:
            _answer_cache[ck] = answer
            if len(_answer_cache) > 64:
                oldest = next(iter(_answer_cache))
                del _answer_cache[oldest]
        return answer

    def query_stream(self, question: str, context=None, history=None):
        if context:
            yield from self._ask_groq_stream(question, context, history)
            return
        if self._is_about_self(question):
            yield from self._ask_groq_stream(question, CAPABILITIES_DESC, history)
            return
        ck = self._cache_key(question)
        if history is None and ck in _answer_cache:
            yield _answer_cache[ck]
            return
        results = self._search_all(question)
        full = ""
        for token in self._ask_groq_stream(question, results, history):
            full += token
            yield token
        if history is None:
            _answer_cache[ck] = full
            if len(_answer_cache) > 64:
                oldest = next(iter(_answer_cache))
                del _answer_cache[oldest]

    def _search_all(self, question: str):
        seen = set()
        combined = []

        # 0. Direct article number lookup (highest priority)
        try:
            article_results = self._search_by_article_number(question)
            for r in article_results:
                doc_id = f"{r['law']}_{r['article']}"
                if doc_id not in seen:
                    seen.add(doc_id)
                    combined.append(r)
        except Exception as e:
            print(f"Article number search error: {e}")

        # 1. JSON keyword search (best for Arabic legal content)
        try:
            json_results = self._search_json_files(question)
            for r in json_results:
                doc_id = f"{r['law']}_{r['article']}"
                if doc_id not in seen:
                    seen.add(doc_id)
                    combined.append(r)
        except Exception as e:
            print(f"JSON search error: {e}")

        # 2. Supplement with close ChromaDB vector matches if < 3 results
        if len(combined) < 3:
            try:
                collection = self._get_collection()
                embedding = self._generate_embedding(question)
                chroma_results = collection.query(
                    query_embeddings=[embedding],
                    n_results=5,
                )
                if chroma_results["documents"] and chroma_results["documents"][0]:
                    for i, doc in enumerate(chroma_results["documents"][0]):
                        dist = chroma_results["distances"][0][i] if chroma_results.get("distances") else 1.0
                        if dist < 1.2:
                            meta = chroma_results["metadatas"][0][i] if chroma_results["metadatas"] else {}
                            doc_id = f"{meta.get('law','')}_{meta.get('article_number','')}"
                            if doc_id not in seen:
                                seen.add(doc_id)
                                combined.append({
                                    "law": meta.get("law", "unknown"),
                                    "article": meta.get("article_number", ""),
                                    "chapter": meta.get("chapter", ""),
                                    "content": doc,
                                })
            except Exception as e:
                print(f"ChromaDB search error: {e}")

        # 3. Supabase as last resort
        if not combined and supabase:
            try:
                embedding = self._generate_embedding(question)
                rpc_result = supabase.rpc(
                    "match_documents",
                    {"query_embedding": embedding, "match_threshold": 0.3, "match_count": 5}
                ).execute()
                if rpc_result.data:
                    for doc in rpc_result.data:
                        meta = doc.get("metadata", {})
                        if isinstance(meta, str):
                            try:
                                meta = json.loads(meta)
                            except (json.JSONDecodeError, TypeError):
                                meta = {}
                        doc_id = f"{meta.get('law','')}_{meta.get('article_number','')}"
                        if doc_id not in seen:
                            seen.add(doc_id)
                            combined.append({
                                "law": meta.get("law", "unknown"),
                                "article": meta.get("article_number", ""),
                                "chapter": meta.get("chapter", ""),
                                "content": doc.get("content", ""),
                            })
            except Exception as e:
                print(f"Supabase search error: {e}")

        # 4. Search jurisprudence (court decisions)
        if len(combined) < 3:
            try:
                jur_results = self._search_jurisprudence(question)
                for r in jur_results:
                    doc_id = f"jur_{r['article']}"
                    if doc_id not in seen:
                        seen.add(doc_id)
                        combined.append(r)
            except Exception as e:
                print(f"Jurisprudence search error: {e}")

        return combined[:5]

    _laws_cache = None
    _laws_by_number = None
    _jurisprudence_cache = None

    @staticmethod
    def _normalize_arabic(text: str) -> str:
        text = text.replace("\u0623", "\u0627").replace("\u0625", "\u0627").replace("\u0622", "\u0627")
        text = text.replace("\u0649", "\u064a").replace("\u0629", "\u0647")
        text = text.replace("\u064b", "").replace("\u064c", "").replace("\u064d", "").replace("\u064e", "").replace("\u064f", "").replace("\u0650", "").replace("\u0651", "").replace("\u0652", "")
        text = text.replace("\u0640", "").replace("\u0653", "").replace("\u0654", "").replace("\u0655", "")
        return text.lower().strip()

    @staticmethod
    def _extract_words(text: str) -> list:
        import re
        text = LegalAgent._normalize_arabic(text)
        words = re.findall(r"[\u0600-\u06ff\w]+", text.lower())
        return [w for w in words if len(w) > 1]

    def _load_all_laws(self):
        if LegalAgent._laws_cache is not None:
            return LegalAgent._laws_cache
        articles = []
        by_number = {}
        laws_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "laws")
        if not os.path.isdir(laws_dir):
            return articles
        for fname in os.listdir(laws_dir):
            if not fname.endswith(".json"):
                continue
            law_key = fname.replace(".json", "")
            fpath = os.path.join(laws_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for article in data.get("articles", []):
                    content = article.get("content", "")
                    if content:
                        law_name = LAW_NAMES.get(law_key, law_key)
                        entry = {
                            "law": law_key,
                            "article": str(article.get("number", "")),
                            "content": content,
                        }
                        articles.append(entry)
                        num = str(article.get("number", "")).strip()
                        if num:
                            by_number.setdefault(law_key, {})[num] = entry
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        LegalAgent._laws_cache = articles
        LegalAgent._laws_by_number = by_number
        return articles

    def _search_by_article_number(self, question: str):
        import re
        match = re.search(r"\u0627\u0644\u0645\u0627\u062f\u0629\s+(\d+)", question)
        if not match:
            match = re.search(r"article\s+(\d+)", question, re.IGNORECASE)
            if not match:
                match = re.search(r"\u0641\u0635\u0644\s+(\d+)", question)
        if match:
            num = match.group(1)
            if LegalAgent._laws_by_number is None:
                self._load_all_laws()
            by_number = LegalAgent._laws_by_number or {}
            for law_key, articles in by_number.items():
                if num in articles:
                    a = articles[num]
                    return [{
                        "law": a["law"],
                        "article": a["article"],
                        "chapter": "",
                        "content": a["content"],
                        "score": 1.0,
                    }]
        return []

    def _search_json_files(self, question: str):
        all_articles = self._load_all_laws()
        q_words = self._extract_words(question)
        if not q_words:
            return []
        q_set = set(q_words)
        q_len = len(q_words)
        results = []
        for a in all_articles:
            c_words = self._extract_words(a["content"])
            if not c_words:
                continue
            c_set = set(c_words)
            overlap = len(q_set & c_set)
            if overlap == 0:
                continue
            term_score = overlap / max(q_len, 1)
            phrase_matches = 0
            for i in range(len(q_words) - 1):
                phrase = q_words[i] + " " + q_words[i + 1]
                if phrase in a["content"].lower():
                    phrase_matches += 1
            phrase_boost = phrase_matches * 0.15
            length_factor = min(1.0, len(c_words) / 50)
            score = term_score + phrase_boost + length_factor * 0.1
            results.append({
                "law": a["law"],
                "article": a["article"],
                "chapter": "",
                "content": a["content"],
                "score": score,
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:5]

    def _load_jurisprudence(self):
        if LegalAgent._jurisprudence_cache is not None:
            return LegalAgent._jurisprudence_cache
        decisions = []
        fpath = os.path.join(os.path.dirname(__file__), "..", "..", "data", "judgements", "juricaf_decisions.json")
        if not os.path.exists(fpath):
            return decisions
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for i, d in enumerate(data):
                title = d.get("title", "")
                desc = d.get("description", "")
                if desc:
                    decisions.append({
                        "law": "jurisprudence",
                        "article": str(i + 1),
                        "title": title,
                        "content": f"{title}\n{desc}",
                        "link": d.get("link", ""),
                        "date": d.get("date", ""),
                    })
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Jurisprudence load error: {e}")
        LegalAgent._jurisprudence_cache = decisions
        return decisions

    def _search_jurisprudence(self, question: str):
        all_decisions = self._load_jurisprudence()
        if not all_decisions:
            return []
        q_words = self._extract_words(question)
        q_lower = question.lower()
        q_set = set(q_words) if q_words else set()
        results = []
        for d in all_decisions:
            c_words = self._extract_words(d["content"])
            score = 0.0
            if q_set and c_words:
                overlap = len(q_set & set(c_words))
                score = overlap / max(len(q_words), 1)
            if "title" in d and d["title"]:
                t_lower = d["title"].lower()
                if any(kw in t_lower for kw in ["commercial", "commerciale"]):
                    if any(kw in q_lower for kw in ["تجاري", "تجارية", "شركة", "شركات", "commercial"]):
                        score += 0.3
                if any(kw in t_lower for kw in ["social", "sociale"]):
                    if any(kw in q_lower for kw in ["اجتماعي", "شغل", "عمل", "أجير", "social"]):
                        score += 0.3
                if any(kw in t_lower for kw in ["civile", "civil"]):
                    if any(kw in q_lower for kw in ["مدني", "مسؤولية", "تعويض", "civil"]):
                        score += 0.3
                if any(kw in t_lower for kw in ["criminelle", "criminal", "penal"]):
                    if any(kw in q_lower for kw in ["جنائي", "جنحة", "جناية", "عقوبة", "penal"]):
                        score += 0.3
                if any(kw in t_lower for kw in ["familiale", "famille"]):
                    if any(kw in q_lower for kw in ["أسرة", "زواج", "طلاق", "نفقة", "family"]):
                        score += 0.3
            if score > 0:
                results.append({
                    "law": "jurisprudence",
                    "article": d["article"],
                    "chapter": "",
                    "content": d["content"][:800],
                    "score": score,
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:3]

    def _build_messages(self, question: str, context, history=None):
        messages = [{"role": "system", "content": DARIJA_PROMPT_SHORT}]
        if history and isinstance(history, list) and len(history) > 0:
            for msg in history:
                if msg.get("role") in ("user", "assistant"):
                    messages.append(msg)
        if isinstance(context, list) and context:
            context_text = "\n\n".join(
                f"[{c['law']} - المادة {c['article']}]\n{c['content']}"
                for c in context[:5]
            )
            user_content = f"""هاذي هي المعلومات القانونية لي خاصك تعتمد عليها فالجواب ديالك. استشهد بيهم بشكل دقيق وذكر رقم المادة والقانون فكل مرة:

{context_text}

سؤال: {question}"""
        elif isinstance(context, str) and context.strip():
            user_content = f"المعلومات:\n{context}\n\nسؤال: {question}"
        else:
            user_content = f"سؤال: {question}"
        messages.append({"role": "user", "content": user_content})
        return messages

    def _demo_answer(self, question: str):
        for keyword, answer in DEMO_ANSWERS.items():
            if keyword in question:
                return answer
        return DEMO_FALLBACK

    def _ask_groq(self, question: str, context, history=None):
        if self.is_demo:
            return self._demo_answer(question)
        messages = self._build_messages(question, context, history)
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.5,
                max_tokens=1536,
            )
            answer = response.choices[0].message.content
            if len(answer) > 2000:
                answer = answer[:2000]
            return answer
        except Exception as e:
            return f"عفوا، عندي مشكل تقني: {str(e)}"

    def _ask_groq_stream(self, question: str, context, history=None):
        if self.is_demo:
            for word in self._demo_answer(question).split(" "):
                yield word + " "
                time.sleep(0.03)
            return
        messages = self._build_messages(question, context, history)
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.5,
                max_tokens=1536,
                stream=True,
            )
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            yield f"عفوا، عندي مشكل تقني: {str(e)}"

    def admin_stats(self):
        stats = {"total_articles": 0, "laws": {}, "jurisprudence": 0}
        for law_key, law_name in LAW_NAMES.items():
            stats["laws"][law_key] = {"name": law_name, "articles": 0}
        try:
            collection = chroma_client.get_collection("moroccan_laws")
            stats["total_articles"] = collection.count()
        except Exception:
            pass
        laws_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "laws")
        if os.path.isdir(laws_dir):
            total = 0
            for fname in os.listdir(laws_dir):
                if not fname.endswith(".json"):
                    continue
                law_key = fname.replace(".json", "")
                fpath = os.path.join(laws_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    count = len(data.get("articles", []))
                    if law_key in stats["laws"]:
                        stats["laws"][law_key]["articles"] = count
                    total += count
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
            if stats["total_articles"] == 0:
                stats["total_articles"] = total
        jur_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "judgements", "juricaf_decisions.json")
        if os.path.exists(jur_path):
            try:
                with open(jur_path, "r", encoding="utf-8") as f:
                    jur_data = json.load(f)
                stats["jurisprudence"] = len(jur_data)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        stats["gov"] = fetch_gov_stats()
        return stats


agent = LegalAgent()
