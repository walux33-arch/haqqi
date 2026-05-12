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
}

# Simple answer cache (LRU: 64 entries)
_answer_cache = {}


DARIJA_PROMPT_SHORT = """نت حقي، مساعد قانوني مغربي بالدارجة. كاتجاوب على أي سؤال كاين.

القواعد:
- جاوب بالدارجة المغربية (داريجا)
- إذا كان السؤال قانوني، استعمل المصادر القانونية وعيط على المادة والقانون
- إذا كان السؤال عام، جاوب من معلوماتك العامة
- جاوب باختصار (جملتين ل 6 جمل)
- ما تعطيش استشارة رسمية (قل "هاد معلومات عامة، راجع محامي")
- جاوب دائما، ما تقولش ما عرفتش\""""


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

    def query(self, question: str, context: str = None):
        if context:
            return self._ask_groq(question, context)
        ck = self._cache_key(question)
        if ck in _answer_cache:
            return _answer_cache[ck]
        results = self._search_all(question)
        answer = self._ask_groq(question, results)
        _answer_cache[ck] = answer
        if len(_answer_cache) > 64:
            oldest = next(iter(_answer_cache))
            del _answer_cache[oldest]
        return answer

    def query_stream(self, question: str, context: str = None):
        if context:
            yield from self._ask_groq_stream(question, context)
            return
        ck = self._cache_key(question)
        if ck in _answer_cache:
            yield _answer_cache[ck]
            return
        results = self._search_all(question)
        full = ""
        for token in self._ask_groq_stream(question, results):
            full += token
            yield token
        _answer_cache[ck] = full
        if len(_answer_cache) > 64:
            oldest = next(iter(_answer_cache))
            del _answer_cache[oldest]

    def _search_all(self, question: str):
        seen = set()
        combined = []

        # 1. JSON keyword search first (best for Arabic legal content)
        try:
            json_results = self._search_json_files(question)
            for r in json_results:
                doc_id = f"{r['law']}_{r['article']}"
                if doc_id not in seen:
                    seen.add(doc_id)
                    combined.append(r)
        except Exception as e:
            print(f"JSON search error: {e}")

        # 2. Supplement with close ChromaDB vector matches if needed
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

        return combined[:5]

    _laws_cache = None

    def _load_all_laws(self):
        if LegalAgent._laws_cache is not None:
            return LegalAgent._laws_cache
        articles = []
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
                        articles.append({
                            "law": law_key,
                            "article": article.get("number", ""),
                            "content": content,
                        })
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        LegalAgent._laws_cache = articles
        return articles

    def _search_json_files(self, question: str):
        all_articles = self._load_all_laws()
        q_words = set(question.lower().split())
        if not q_words:
            return []
        results = []
        for a in all_articles:
            c_words = set(a["content"].lower().split())
            overlap = len(q_words & c_words)
            if overlap > 0:
                results.append({
                    "law": a["law"],
                    "article": a["article"],
                    "chapter": "",
                    "content": a["content"],
                    "score": overlap / max(len(q_words), 1),
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:5]

    def _build_messages(self, question: str, context):
        if isinstance(context, list) and context:
            context_text = "\n\n".join(
                f"[{c['law']} - المادة {c['article']}]\n{c['content']}"
                for c in context[:3]
            )
            user_content = f"المعلومات القانونية:\n{context_text}\n\nسؤال: {question}"
        elif isinstance(context, str) and context.strip():
            user_content = f"المعلومات:\n{context}\n\nسؤال: {question}"
        else:
            user_content = f"سؤال: {question}"
        return [
            {"role": "system", "content": DARIJA_PROMPT_SHORT},
            {"role": "user", "content": user_content},
        ]

    def _demo_answer(self, question: str):
        for keyword, answer in DEMO_ANSWERS.items():
            if keyword in question:
                return answer
        return DEMO_FALLBACK

    def _ask_groq(self, question: str, context):
        if self.is_demo:
            return self._demo_answer(question)
        messages = self._build_messages(question, context)
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.3,
                max_tokens=512,
            )
            answer = response.choices[0].message.content
            if len(answer) > 600:
                answer = answer[:600]
            return answer
        except Exception as e:
            return f"عفوا، عندي مشكل تقني: {str(e)}"

    def _ask_groq_stream(self, question: str, context):
        if self.is_demo:
            for word in self._demo_answer(question).split(" "):
                yield word + " "
                time.sleep(0.03)
            return
        messages = self._build_messages(question, context)
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.3,
                max_tokens=512,
                stream=True,
            )
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            yield f"عفوا، عندي مشكل تقني: {str(e)}"

    def admin_stats(self):
        stats = {"total_articles": 0, "laws": {}}
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
        stats["gov"] = fetch_gov_stats()
        return stats


agent = LegalAgent()
