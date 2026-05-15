# حقي (Haqqi) — Moroccan Legal AI Platform

> **حقي** is an AI-powered legal assistant for Moroccan citizens, answering legal questions in **Moroccan Darija** using Retrieval-Augmented Generation (RAG) over 3,777 articles from 5 Moroccan law codes.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-orange)](https://groq.com)

---

## Features ✨

| Feature | Description |
|---------|-------------|
| **🤖 Darija Legal Chat** | Ask legal questions in Moroccan Darija, get answers citing specific articles |
| **📚 3,777 Legal Articles** | 5 codes: Penal, Civil Obligations, Commercial, Family, Labour |
| **⚡ RAG Pipeline** | ChromaDB → Supabase (pgvector) → JSON keyword → Groq LLM with 3 fallback levels |
| **⚡ Streaming Responses** | See answers appear word-by-word — first token in ~1s |
| **📄 PDF Contract Generation** | Generate rent, employment, and partnership contracts |
| **⚖️ Court Decisions** | 30+ Moroccan Cassation decisions with search/filter |
| **🔐 Auth** | Email/password via Supabase Auth |
| **📱 PWA** | Installable as mobile app, works offline via service worker |
| **🐳 Docker** | Production-ready container with health checks |
| **🌐 RTL UI** | Full Arabic right-to-left support with Tajawal font |

---

## Architecture 🏗️

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (PWA)                         │
│          Jinja2 Templates + Tailwind CSS                 │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / SSE Stream
┌──────────────────────▼──────────────────────────────────┐
│              FastAPI (Python 3.12)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │  Auth    │  │  Chat    │  │  Contracts API        │   │
│  │  Routes  │  │  (SSE)   │  │  PDF Generation       │   │
│  └──────────┘  └────┬─────┘  └──────────────────────┘   │
└──────────────────────┼──────────────────────────────────┘
                       │
    ┌──────────────────┼──────────────────────┐
    ▼                  ▼                      ▼
┌─────────┐   ┌─────────────┐   ┌────────────────────┐
│ChromaDB │   │  Supabase   │   │   Groq API          │
│(vector) │   │(pgvector +  │   │   (Llama 3.3 70B)   │
│ local   │   │  Auth)      │   │   cloud             │
└─────────┘   └─────────────┘   └────────────────────┘
    │               │
    ▼               ▼
┌────────────────────────┐
│  JSON Law Files        │
│  (keyword fallback)    │
└────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Frontend** | Jinja2, Tailwind CSS (CDN), Alpine.js |
| **LLM** | Groq API — Llama 3.3 70B (streaming) |
| **Vector Store** | ChromaDB (local) + Supabase pgvector |
| **Embeddings** | paraphrase-multilingual-MiniLM-L12-v2 |
| **Auth** | Supabase Auth (email/password, cookies) |
| **PDF** | PyMuPDF |
| **Infra** | Docker, docker-compose |

---

## Quick Start 🚀

### Prerequisites
- Python 3.12+
- (Optional) [Groq API key](https://console.groq.com) for LLM answers
- (Optional) [Supabase account](https://supabase.com) for cloud vector store

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/haqqi.git
cd haqqi
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys (see below for demo mode)
```

### 3. Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Open http://localhost:8000
```

### Demo Mode 🔌

**No API keys needed.** If `GROQ_API_KEY` is not set, Haqqi runs in **demo mode** with pre-written answers for common topics (marriage, divorce, labour, rent, companies, inheritance). All pages, PWA, and PDF contracts work fully.

### Docker

```bash
docker compose up -d
# Open http://localhost:8000
```

---

## Project Structure 📁

```
haqqi/
├── app/
│   ├── main.py              # FastAPI app + routes
│   ├── api/
│   │   └── endpoints.py     # REST API (chat, stats, contracts, etc.)
│   ├── agent/
│   │   └── legal_agent.py   # RAG pipeline (ChromaDB → Supabase → JSON → Groq)
│   ├── auth.py              # Supabase Auth helper
│   ├── contracts/
│   │   └── generator.py     # PDF contract generation (PyMuPDF)
│   ├── static/              # PWA icons, manifest, service worker
│   └── templates/           # Jinja2 HTML templates
│       ├── index.html       # Chat homepage
│       ├── judgements.html  # Court decisions
│       ├── contracts.html   # PDF contract forms
│       ├── auth.html        # Login/Signup
│       ├── admin.html       # Admin dashboard
│       └── _navbar.html     # Shared navigation
├── data/
│   ├── laws/                # 5 Moroccan law codes (JSON)
│   └── judgements/          # Court decisions
├── scripts/                 # Data loading utilities
├── chroma_db/               # Local vector store (gitignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## API Endpoints 🌐

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Ask a legal question (streaming response) |
| GET | `/api/stats` | System statistics (articles, laws) |
| GET | `/api/entities` | Moroccan business entities |
| GET | `/api/judgements` | Search court decisions |
| GET | `/api/contracts` | List contract templates |
| POST | `/api/contracts/generate` | Generate PDF contract |
| GET | `/api/health` | Health check |

---

## Data 📊

### Legal Codes (3,777 articles)

| Code | Articles | Description |
|------|----------|-------------|
| Penal | 705 | القانون الجنائي |
| DOC | 1,274 | ظهيرة الالتزامات والعقود |
| Commercial | 809 | القانون التجاري |
| Family | 400 | مدونة الأسرة |
| Labour | 589 | مدونة الشغل |

### Source
All texts sourced from [mandili.net](https://mandili.net) (full Arabic, public access). Each article is stored with embeddings in both ChromaDB (local) and Supabase pgvector (cloud).

---

## Roadmap 🗺️

- [x] MVP — 5 law codes, RAG pipeline, chat UI
- [x] PDF contract generation (rent, employment, partnership)
- [x] PWA — installable, cache-first offline
- [x] Auth — Supabase Auth (email/password)
- [x] Streaming responses
- [x] Demo mode (no API keys needed)
- [ ] WhatsApp Bot integration
- [ ] 300+ court decisions
- [ ] 20+ laws & regulations
- [ ] Legal glossary
- [ ] Rate limiting & Captcha
- [ ] Mobile app (Flutter)

---

## Business 💼

**Target Market**: 37M+ Moroccan citizens, 70%+ Darija speakers
**Problem**: Legal information is scattered, in classical Arabic/French, and expensive ($50-200/hr for lawyers)
**Solution**: Free AI legal assistant in Darija with verified sources

### Monetization Paths
1. **Freemium** — Free basic queries, premium for detailed analysis
2. **Professional** — Paid API for law firms (white-label)
3. **Document Automation** — Paid contract generation (10+ templates)
4. **Enterprise** — Corporate compliance tool for Moroccan companies

---

## License 📝

MIT License — see [LICENSE](LICENSE)

---

## Contact 📬

- **Project**: Haqqi — المساعد القانوني المغربي
- **Built with**: Python, FastAPI, Groq, ChromaDB, Supabase

---

> **إخلاء مسؤولية**: حقي هو مساعد معلومات قانونية ولا يشكل استشارة قانونية رسمية. المعلومات المقدمة للاسترشاد فقط.
