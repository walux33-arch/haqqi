import json, os, re, uuid, time, tempfile
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from app.agent.legal_agent import agent, groq_client
from app.contracts.generator import generate_pdf, get_contract_templates

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# ─── Conversation Memory ───
conversations = {}  # session_id -> list of messages
MAX_HISTORY = 20    # keep last 20 messages per session

class QueryRequest(BaseModel):
    question: str
    context: str = None
    session_id: str = None
    history: list = None  # previous messages [{role, content}]


@router.post("/chat")
async def chat(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="السؤال فاضي")

    # Session management
    session_id = req.session_id or uuid.uuid4().hex[:12]
    if session_id not in conversations:
        conversations[session_id] = []

    # Store user message
    conversations[session_id].append({"role": "user", "content": req.question})

    # Use client history (has user+assistant) or fall back to server storage
    history = req.history if req.history else conversations[session_id]
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    return StreamingResponse(
        agent.query_stream(req.question, req.context, history),
        media_type="text/plain",
        headers={"X-Session-Id": session_id},
    )


@router.get("/chat/history/{session_id}")
async def get_history(session_id: str):
    msgs = conversations.get(session_id, [])
    return {"session_id": session_id, "messages": msgs, "count": len(msgs)}


@router.post("/chat/new")
async def new_chat():
    sid = uuid.uuid4().hex[:12]
    conversations[sid] = []
    return {"session_id": sid}


@router.post("/chat/clear")
async def clear_session(data: dict):
    sid = data.get("session_id")
    if sid and sid in conversations:
        del conversations[sid]
    return {"status": "cleared"}


@router.get("/stats")
async def stats():
    return agent.admin_stats()


@router.get("/entities")
async def entities():
    path = os.path.join(DATA_DIR, "incorporation", "morocco_entities.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/judgements")
async def judgements(
    search: str = Query("", max_length=200),
    chamber: str = Query("", max_length=50),
    year: int = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
):
    path = os.path.join(DATA_DIR, "judgements", "juricaf_decisions.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    def parse_chamber(title):
        m = re.search(r"Chambre\s+([^,]+)", title)
        return m.group(1).strip() if m else ""

    def parse_year(date_str):
        parts = date_str.split()
        for p in parts:
            if p.isdigit() and len(p) == 4:
                return int(p)
        return None

    results = []
    for d in data:
        c = parse_chamber(d["title"])
        y = parse_year(d["date"])
        if search and search.lower() not in d["title"].lower() and search.lower() not in d["description"].lower():
            continue
        if chamber and chamber != c:
            continue
        if year is not None and y != year:
            continue
        results.append({**d, "chamber": c, "year": y})

    chambers = sorted(set(parse_chamber(d["title"]) for d in data))
    years = sorted(set(parse_year(d["date"]) for d in data if parse_year(d["date"])), reverse=True)

    total = len(results)
    start = (page - 1) * per_page
    items = results[start:start + per_page]

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "filters": {"chambers": chambers, "years": years},
    }


@router.get("/contracts")
async def list_contracts():
    return get_contract_templates()


class ContractRequest(BaseModel):
    contract_type: str
    data: dict


@router.post("/contracts/generate")
async def generate_contract(req: ContractRequest):
    try:
        pdf_bytes = generate_pdf(req.contract_type, req.data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={req.contract_type}.pdf"},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ تقني: {str(e)}")


class PleadingRequest(BaseModel):
    type: str  # افتتاحية, دفاع, استئناف, جوابية, عريضة
    case_subject: str
    plaintiff: str = ""
    defendant: str = ""
    court: str = ""
    case_number: str = ""
    facts: str = ""
    arguments: str = ""
    context: str = None

PLEADING_TYPES = {
    "افتتاحية": "مقال افتتاحي للدعوى",
    "دفاع": "مذكرة دفاع",
    "استئناف": "مقال استئنافي",
    "جوابية": "مذكرة جوابية",
    "عريضة": "عريضة دعوى",
}

@router.post("/pleadings/generate")
async def generate_pleading(req: PleadingRequest):
    if req.type not in PLEADING_TYPES:
        raise HTTPException(status_code=400, detail="نوع المقال غير معروف")
    title = PLEADING_TYPES[req.type]

    # Build the prompt for legal drafting
    system_prompt = """أنت مساعد قانوني مغربي خبير فكتابة المقالات القانونية (العرائض والمذكرات).
اكتب بصيغة رسمية قانونية محترمة بالفصحى. استعمل المصطلحات القانونية المغربية.
حدد النصوص القانونية المعتمدة (القانون + المادة).
اكتب بصيغة: "حيث إن" و "بناء عليه" (المنهجية القانونية المغربية)."""

    agent_prompt = f"""اكتب {title} باللغة العربية الفصحى القانونية.

معلومات القضية:
- الموضوع: {req.case_subject}
- المدعي/المطالب: {req.plaintiff or 'غير محدد'}
- المدعى عليه/المطلوب: {req.defendant or 'غير محدد'}
- المحكمة: {req.court or 'غير محدد'}
- رقم الملف: {req.case_number or 'غير محدد'}
- الوقائع: {req.facts or 'غير محدد'}
- الوسائل الدفاعية/الأسانيد: {req.arguments or 'غير محدد'}

القوانين المستخرجة من البحث:"""

    # Search for relevant laws
    legal_context = agent._search_all(req.case_subject)
    if legal_context:
        for c in legal_context[:5]:
            agent_prompt += f"\n- {c.get('law','')} - المادة {c.get('article','')}: {c.get('content','')[:300]}"
    else:
        agent_prompt += "\nلم يتم العثور على نصوص محددة. استعمل القواعد القانونية العامة."

    agent_prompt += f"\n\nاكتب {title} كاملا ومنسقا بالمغرب."

    if groq_client:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": agent_prompt},
            ],
            temperature=0.4,
            max_tokens=2048,
        )
        text = response.choices[0].message.content
    else:
        text = f"""بسم الله الرحمن الرحيم

{title}

بناء على الفصل ... من الظهير الشريف ... والقانون ... المادة ...

حيث إن وقائع القضية تتمثل في: {req.facts or req.case_subject}

وحيث إن الثابت من أوراق الملف أن ...

وحيث إن الفصل ... من القانون ينص على أن ...

بناء عليه،

يلتمس/يلتمس دفاع {req.plaintiff or 'الطرف'} قبول هذا المقال شكلا وفي الجوهر والحكم بـ ...

وحرر بـ {req.court or 'المحكمة المختصة'} في ..."""

    return {"type": req.type, "title": title, "text": text}

@router.get("/pleadings/types")
async def pleading_types():
    return [{"key": k, "label": v} for k, v in PLEADING_TYPES.items()]

@router.get("/health")
async def health():
    return {"status": "ok", "service": "haqqi"}


# ─── Ingestion API ───

from app.ingestion import pipeline as ingestion_pipeline


@router.post("/ingestion/upload")
async def ingest_upload(file: UploadFile = File(...)):
    """Upload a document (PDF, image, TXT, DOCX) for ingestion."""
    ext = os.path.splitext(file.filename or "doc.pdf")[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        doc = ingestion_pipeline.ingest_file(
            tmp_path,
            title=os.path.splitext(file.filename or "document")[0],
        )
        return doc.to_dict()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.post("/ingestion/url")
async def ingest_url(data: dict):
    """Import a document from a URL."""
    url = data.get("url", "")
    title = data.get("title", "")
    if not url:
        raise HTTPException(status_code=400, detail="URL مطلوب")
    doc = ingestion_pipeline.ingest_url(url, title=title)
    return doc.to_dict()


@router.post("/ingestion/text")
async def ingest_text(data: dict):
    """Ingest pasted text directly."""
    text = data.get("text", "")
    title = data.get("title", "")
    if not text:
        raise HTTPException(status_code=400, detail="النص مطلوب")
    doc = ingestion_pipeline.ingest_text(text, title=title)
    return doc.to_dict()


@router.get("/ingestion/history")
async def ingestion_history(limit: int = 20):
    return {"documents": ingestion_pipeline.get_history(limit=limit)}


@router.get("/ingestion/stats")
async def ingestion_stats():
    return ingestion_pipeline.get_stats()


# ─── Scraper API ───

from app.ingestion.scrapers.adala import SCRAPERS


@router.get("/scrapers")
async def list_scrapers():
    return {
        name: {
            "name": s.name,
            "label": s.label,
            "base_url": s.base_url,
            "stats": s.stats(),
        }
        for name, s in SCRAPERS.items()
    }


@router.post("/scrapers/run")
async def run_scraper(data: dict):
    """Run a specific scraper."""
    name = data.get("scraper", "")
    keyword = data.get("keyword", "")
    max_items = min(data.get("max_items", 10), 50)
    if name not in SCRAPERS:
        raise HTTPException(status_code=400, detail=f"Scraper '{name}' غير معروف")
    scraper = SCRAPERS[name]
    results = scraper.scrape_and_ingest(keyword=keyword, max_items=max_items)
    return {
        "scraper": name,
        "keyword": keyword,
        "results": results,
    }


@router.post("/scrapers/ingest-urls")
async def ingest_scraper_urls(data: dict):
    """Ingest specific URLs from a scraper source."""
    scraper_name = data.get("scraper", "adala")
    urls = data.get("urls", [])
    if scraper_name not in SCRAPERS:
        raise HTTPException(status_code=400, detail=f"Scraper '{scraper_name}' غير معروف")
    scraper = SCRAPERS[scraper_name]
    if hasattr(scraper, "ingest_urls"):
        results = scraper.ingest_urls(urls)
        return {"results": results}
    return {"error": "هذا المصدر لا يدعم استيراد الروابط يدوياً"}
