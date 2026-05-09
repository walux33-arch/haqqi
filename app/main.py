import os
import time
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

template_dir = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(template_dir))

app = FastAPI(title="حقي - Haqqi", version="1.0.0")

from fastapi.staticfiles import StaticFiles

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ─── Rate Limiter ───
_rate_limit = defaultdict(list)
RATE_LIMIT = 20  # requests
RATE_WINDOW = 60  # seconds

def _check_rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    _rate_limit[ip] = [t for t in _rate_limit[ip] if now - t < RATE_WINDOW]
    if len(_rate_limit[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="بزاف ديال الطلبات. هدي شوية وحاول مرة أخرى.")
    _rate_limit[ip].append(now)

# ─── Rate Limit Middleware ───
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.url.path != "/api/health":
        _check_rate_limit(request)
    return await call_next(request)

from app.api.endpoints import router as api_router
app.include_router(api_router, prefix="/api")

from app.whatsapp.routes import router as whatsapp_router
app.include_router(whatsapp_router, prefix="/api")

# ─── SEO & Static Pages ───

@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return """User-agent: *
Allow: /
Sitemap: https://haqqi.ma/sitemap.xml
"""

@app.get("/sitemap.xml", response_class=PlainTextResponse)
async def sitemap():
    return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://haqqi.ma/</loc><priority>1.0</priority></url>
  <url><loc>https://haqqi.ma/judgements</loc><priority>0.8</priority></url>
  <url><loc>https://haqqi.ma/contracts</loc><priority>0.8</priority></url>
  <url><loc>https://haqqi.ma/incorporation</loc><priority>0.8</priority></url>
  <url><loc>https://haqqi.ma/about</loc><priority>0.6</priority></url>
  <url><loc>https://haqqi.ma/privacy</loc><priority>0.5</priority></url>
  <url><loc>https://haqqi.ma/disclaimer</loc><priority>0.5</priority></url>
</urlset>
"""

# ─── Custom 404 ───

@app.exception_handler(404)
async def not_found(request: Request, exc):
    return render("404.html")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


def render(template_name: str, **kwargs):
    template = env.get_template(template_name)
    return HTMLResponse(template.render(**kwargs))


def get_user(request: Request):
    token = request.cookies.get("haqqi_token")
    if not token:
        return None
    try:
        return supabase.auth.get_user(token).user
    except Exception:
        return None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_user(request)
    return render("index.html", user=user)


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")
    from app.agent.legal_agent import agent
    stats = agent.admin_stats()
    return render("admin.html", stats=stats, user=user)


@app.get("/judgements", response_class=HTMLResponse)
async def judgements(request: Request):
    user = get_user(request)
    return render("judgements.html", user=user)


@app.get("/incorporation", response_class=HTMLResponse)
async def incorporation(request: Request):
    user = get_user(request)
    return render("incorporation.html", user=user)


@app.get("/contracts", response_class=HTMLResponse)
async def contracts(request: Request):
    user = get_user(request)
    return render("contracts.html", user=user)


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    user = get_user(request)
    return render("privacy.html", user=user)


@app.get("/disclaimer", response_class=HTMLResponse)
async def disclaimer(request: Request):
    user = get_user(request)
    return render("disclaimer.html", user=user)


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    user = get_user(request)
    return render("about.html", user=user)


@app.get("/whatsapp", response_class=HTMLResponse)
async def whatsapp_page(request: Request):
    user = get_user(request)
    return render("whatsapp.html", active="whatsapp", user=user)


@app.get("/pitch", response_class=HTMLResponse)
async def pitch():
    path = os.path.join(os.path.dirname(__file__), "templates", "pitch.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/pitch/ar", response_class=HTMLResponse)
async def pitch_ar():
    path = os.path.join(os.path.dirname(__file__), "templates", "pitch_ar.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ─── Auth Routes ───

@app.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_user(request)
    return render("auth.html", mode="login", user=user)


@app.get("/auth/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    user = get_user(request)
    return render("auth.html", mode="signup", user=user)


@app.post("/auth/login")
async def login(request: Request):
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if not res.session:
            raise HTTPException(status_code=401, detail="البريد أو كلمة السر غالطة")
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="haqqi_token", value=res.session.access_token, httponly=True, max_age=86400*7)
        return response
    except Exception as e:
        raise HTTPException(status_code=401, detail="البريد أو كلمة السر غالطة")


@app.post("/auth/signup")
async def signup(request: Request):
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        res = supabase.auth.sign_up({"email": email, "password": password})
        return {"message": "تم التسجيل! تأكد من بريدك الإلكتروني"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("haqqi_token")
    return response


@app.get("/api/me")
async def get_me(request: Request):
    user = get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="غير مسجل")
    return {"email": user.email, "id": user.id, "created_at": user.created_at}
