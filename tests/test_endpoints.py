import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["GROQ_API_KEY"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_homepage():
    r = client.get("/")
    assert r.status_code == 200
    assert "حقي" in r.text


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


def test_chat_streaming():
    r = client.post("/api/chat", json={
        "question": "شنو هو الزواج",
        "context": "الزواج هو عقد شرعي بين رجل وامرأة"
    })
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    text = r.text
    assert len(text) > 0


def test_chat_empty():
    r = client.post("/api/chat", json={"question": ""})
    assert r.status_code == 400


def test_stats():
    r = client.get("/api/stats")
    assert r.status_code == 200


def test_judgements():
    r = client.get("/api/judgements")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "filters" in data


def test_contracts_list():
    r = client.get("/api/contracts")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    for cid in ("rent", "employment", "partnership"):
        assert cid in data
        assert "title" in data[cid]
        assert "fields" in data[cid]


def test_auth_page():
    r = client.get("/auth/login")
    assert r.status_code == 200
    assert "دخول" in r.text or "login" in r.text.lower()


def test_admin_page_redirect():
    r = client.get("/admin", follow_redirects=False)
    assert r.status_code in (302, 303, 307)
