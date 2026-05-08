"""Authentication helpers for Supabase Auth."""

import os
from functools import wraps
from fastapi import Request, HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


async def get_current_user(request: Request):
    token = request.cookies.get("haqqi_token")
    if not token:
        return None
    try:
        user = supabase.auth.get_user(token)
        return user.user
    except Exception:
        return None


def require_auth(f):
    @wraps(f)
    async def wrapper(request: Request, *args, **kwargs):
        user = await get_current_user(request)
        if not user:
            raise HTTPException(status_code=303, detail="Unauthorized", headers={"Location": "/auth/login"})
        return await f(request, *args, **kwargs)
    return wrapper
