import json, os, re
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from app.agent.legal_agent import agent
from app.contracts.generator import generate_pdf, get_contract_templates

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


class QueryRequest(BaseModel):
    question: str
    context: str = None


@router.post("/chat")
async def chat(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="السؤال فاضي")
    return StreamingResponse(
        agent.query_stream(req.question, req.context),
        media_type="text/plain",
    )


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


@router.get("/health")
async def health():
    return {"status": "ok", "service": "haqqi"}
