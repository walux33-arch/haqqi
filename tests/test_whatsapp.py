import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["GROQ_API_KEY"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""

from app.whatsapp.bot import handle_message, process_twilio_request, twilio_response, WELCOME_MSG, HELP_MSG, TOPICS_MSG


def test_welcome_message():
    resp = handle_message("سلام", "test_sender")
    assert "مرحبا" in resp
    assert "حقي" in resp
    assert "الزواج" in resp


def test_help_message():
    resp = handle_message("مساعدة", "test_sender")
    assert "كيفاش" in resp
    assert "الأوامر" in resp


def test_topics_message():
    resp = handle_message("المواضيع", "test_sender")
    assert "القانون الجنائي" in resp
    assert "مدونة الأسرة" in resp
    assert "مدونة الشغل" in resp


def test_legal_query():
    resp = handle_message("زواج", "test_sender_2")
    assert len(resp) > 10
    assert "زواج" in resp or "الزواج" in resp


def test_session_isolation():
    resp1 = handle_message("زواج", "test_sender_a")
    resp2 = handle_message("زواج", "test_sender_b")
    assert resp1 == resp2


def test_empty_message():
    resp = handle_message("", "test_sender")
    assert len(resp) > 0


def test_twilio_request_processing():
    form = {"Body": "سلام", "From": "whatsapp:+212600000000"}
    answer = process_twilio_request(form)
    assert "مرحبا" in answer


def test_twilio_response_xml():
    xml = twilio_response("مرحبا بك")
    assert "<Response>" in xml
    assert "<Message>" in xml
    assert "مرحبا بك" in xml


def test_unknown_command():
    resp = handle_message("xyz_not_a_real_command_12345", "test_sender")
    assert len(resp) > 0
