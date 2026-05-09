import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from app.whatsapp.bot import process_twilio_request, twilio_response

router = APIRouter()

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "haqqi_verify_2026")


@router.get("/whatsapp/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    body = await request.form()
    form_dict = dict(body)
    answer = process_twilio_request(form_dict)
    xml_resp = twilio_response(answer)
    return Response(content=xml_resp, media_type="application/xml")
