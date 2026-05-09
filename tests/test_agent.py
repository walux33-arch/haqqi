import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["GROQ_API_KEY"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""

from app.agent.legal_agent import LegalAgent, DEMO_ANSWERS, DEMO_FALLBACK


def test_agent_creation():
    agent = LegalAgent()
    assert agent is not None
    assert agent.is_demo


def test_demo_answer_known():
    agent = LegalAgent()
    for keyword in DEMO_ANSWERS:
        answer = agent.query(f"شنو هو {keyword}")
        assert isinstance(answer, str)
        assert len(answer) > 10


def test_demo_answer_unknown():
    agent = LegalAgent()
    answer = agent.query("سؤال عشوائي ما عندوش جواب")
    assert answer == DEMO_FALLBACK


def test_demo_stream():
    agent = LegalAgent()
    tokens = list(agent.query_stream("زواج"))
    combined = "".join(tokens)
    assert len(combined) > 10
    assert "زواج" in combined or "الزواج" in combined


def test_cache():
    agent = LegalAgent()
    a1 = agent.query("زواج")
    a2 = agent.query("زواج")
    assert a1 == a2


def test_admin_stats():
    agent = LegalAgent()
    stats = agent.admin_stats()
    assert "total_articles" in stats
    assert "laws" in stats
    assert "gov" in stats
    assert stats["gov"]["summary"]["total_datasets"] >= 0
    assert stats["gov"]["summary"]["categories_count"] >= 0
