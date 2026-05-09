import os
import json
import time
from datetime import datetime, timedelta, timezone

from app.agent.legal_agent import agent

SESSION_TTL = timedelta(hours=1)
_sessions: dict[str, dict] = {}

WELCOME_MSG = (
    "مرحبا بك في *حقي* 🤖⚖️\n\n"
    "أنا مساعدك القانوني المغربي. كيقدر تسولني على:\n"
    "• الزواج والطلاق (مدونة الأسرة)\n"
    "• العقود والالتزامات\n"
    "• القانون التجاري وتأسيس الشركات\n"
    "• القانون الجنائي\n"
    "• قانون الشغل\n\n"
    "اكتب سؤالك القانوني بالدارجة و غادي نجاوبك."
)

HELP_MSG = (
    "كيفاش كيخدم *حقي*:\n\n"
    "1. اكتب سؤالك القانوني بالدارجة\n"
    "2. حقي كيقرا المصادر القانونية (3,777 مادة)\n"
    "3. كيجاوبك مع ذكر المواد\n\n"
    'مثال: "شنو هي شروط الزواج فالمغرب؟"\n\n'
    "الأوامر:\n"
    "- *مساعدة* - هاد الرسالة\n"
    "- *البداية* - ترحيب\n"
    "- *المواضيع* - لائحة المواضيع"
)

TOPICS_MSG = (
    "المواضيع لي كيقدر يعاونك فيها حقي:\n\n"
    "⚖️ *القانون الجنائي*\n"
    "📜 *ظهيرة الالتزامات والعقود*\n"
    "🏢 *القانون التجاري*\n"
    "👨‍👩‍👧‍👦 *مدونة الأسرة*\n"
    "👷 *مدونة الشغل*\n"
    "🏛️ *الأحكام القضائية*\n"
    "📄 *توليد العقود*\n"
    "🏗️ *تأسيس الشركات*"
)


def _clean_session(sender: str):
    _sessions.pop(sender, None)


def _get_or_create_session(sender: str) -> dict:
    now = datetime.now(timezone.utc)
    expired = [k for k, v in _sessions.items() if now - v.get("created_at", now) > SESSION_TTL]
    for k in expired:
        _clean_session(k)
    if sender not in _sessions:
        _sessions[sender] = {"history": [], "created_at": now}
    return _sessions[sender]


def handle_message(incoming_text: str, sender: str) -> str:
    text = incoming_text.strip()
    session = _get_or_create_session(sender)

    if text in ("البداية", "بداية", "start", "hi", "hello", "سلام", "السلام"):
        return WELCOME_MSG

    if text in ("مساعدة", "مساعدة", "help", "مساعده"):
        return HELP_MSG

    if text in ("المواضيع", "المواضيع", "topics", "مواضيع"):
        return TOPICS_MSG

    if text == "json" and os.getenv("WHATSAPP_DEBUG") == "true":
        return json.dumps({"sender": sender, "session_length": len(session["history"])}, ensure_ascii=False)

    session["history"].append({"role": "user", "content": text, "time": datetime.now(timezone.utc).isoformat()})
    session["history"] = session["history"][-10:]

    try:
        answer = agent.query(text)
    except Exception as e:
        answer = f"عفوا، عندي مشكل تقني: {str(e)}"

    session["history"].append({"role": "assistant", "content": answer, "time": datetime.now(timezone.utc).isoformat()})

    return answer


def process_twilio_request(form_data: dict) -> str:
    from_body = form_data.get("Body", "")
    from_wa = form_data.get("From", "unknown")
    sender = from_wa.replace("whatsapp:", "")
    return handle_message(from_body, sender)


def twilio_response(message: str) -> str:
    import xml.etree.ElementTree as ET
    resp = ET.Element("Response")
    msg = ET.SubElement(resp, "Message")
    msg.text = message
    return ET.tostring(resp, encoding="unicode", xml_declaration=False)
