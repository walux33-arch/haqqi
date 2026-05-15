# Haqqi (حقي) — Fiche Technique
## Assistant Juridique Marocain par IA

---

### 📋 Identification

| Champ | Valeur |
|-------|--------|
| **Produit** | Haqqi (حقي) — Assistant juridique IA |
| **Société** | HaqiTech Inc. |
| **Fondateur** | Al Walid Faouzi |
| **Contact** | contact@haqqi.ma |
| **Version** | 2.0.0 (Mai 2026) |
| **Statut** | MVP fonctionnel — Pré-production |
| **Licence** | Propriétaire HaqiTech |

---

### 🏗 Architecture Technique

```
┌─────────────────────────────────────────────────────────┐
│                     HAQQI PLATFORM                       │
├──────────────┬──────────────┬──────────────┬─────────────┤
│   Frontend   │    API       │  IA/RAG      │   Données   │
│  TailwindCSS │  FastAPI     │  Groq        │  ChromaDB   │
│  Alpine.js   │  OpenAPI     │  Llama 3.3   │  5 697 art. │
│  PWA Ready   │  Streaming   │  70B params  │  30 juris.  │
├──────────────┴──────────────┴──────────────┴─────────────┤
│          Infrastructure : Docker Compose + Caddy          │
│          Embeddings : paraphrase-multilingual-MiniLM-L12-v2│
│          Scraping : Playwright + urllib                   │
│          OCR : Tesseract + pdfplumber                     │
└──────────────────────────────────────────────────────────┘
```

---

### 📊 Base de Connaissance

**5 697+ articles de loi → 11 codes + Constitution :**

| Code | Articles | Poids RAG |
|------|:--------:|:---------:|
| ظهيرة الالتزامات والعقود (DOC) | 1 274 | ⭐⭐⭐ |
| قانون المسطرة الجنائية | 866 | ⭐⭐⭐ |
| القانون التجاري | 809 | ⭐⭐⭐ |
| القانون الجنائي | 705 | ⭐⭐⭐ |
| مدونة الشغل | 589 | ⭐⭐ |
| مدونة الأسرة | 400 | ⭐⭐⭐ |
| قانون التأمينات | 407 | ⭐⭐ |
| قانون الحقوق العينية | 328 | ⭐⭐ |
| قانون حماية المستهلك | 199 | ⭐⭐ |
| الدستور المغربي | 150 | ⭐⭐⭐ (priorité max) |
| **Total** | **5 697+** | |

**Autres données :**
- 30 décisions Cour de Cassation (juricaf)
- 19 procédures administratives (Loi 55.19)
- Scraping live Adala.ma + SGG.ma

---

### ✅ Conformité Réglementaire

| Référentiel | Statut | Détail |
|-------------|:------:|--------|
| **Loi 55.19** | ✅ | 19 procédures, référence Rachad.ma |
| **Loi 09.08** | ✅ | Anonymisation CIN/tél/email/ICE |
| **CNDP** | 🔄 | Audit en cours |
| **Loi 06.07** | ✅ | Anti-abrogation intégré |
| **Art. 5 Constitution** | ⚠️ | Détection Tifinagh basique |
| **RGPD** | 🔄 | Via conformité Loi 09.08 |

---

### 🌐 API Publique (Endpoints)

| Endpoint | Méthode | Description |
|----------|:-------:|-------------|
| `/api/chat` | POST | Chat streaming avec historique |
| `/api/stats` | GET | Statistiques base juridique |
| `/api/health` | GET | Healthcheck |
| `/api/ingestion/upload` | POST | Upload document (PDF/DOCX/TXT) |
| `/api/ingestion/text` | POST | Ingestion texte libre |
| `/api/scrapers/run` | POST | Lancer scraper (adala/sgg) |

**Documentation :** `/docs` (Swagger) | `/redoc` (ReDoc) | `/api/public`

---

### 🖥 Pages Web

| URL | Contenu |
|-----|---------|
| `/` | Dashboard principal |
| `/ministere` | Évaluation stratégique ministère |
| `/ministere/conformite` | Conformité Loi 09.08 |
| `/api/public` | Documentation API publique |
| `/admin/ingestion` | Pipeline ingestion (auth) |
| `/contact` | Contact HaqiTech |

---

### 🚀 Roadmap 2026

| Phase | Période | Livrable |
|-------|---------|----------|
| **Phase 1** (MVP) | Mai 2026 | Chat RAG + 5 697 articles + 19 procédures |
| **Phase 2** | Juin 2026 | Jurisprudence 500+ décisions, embedding arabe |
| **Phase 3** | Juillet 2026 | API gouvernementale, hébergement souverain |
| **Phase 4** | Septembre 2026 | Pilote 2 préfectures, module amazigh complet |
| **Phase 5** | Décembre 2026 | 10 000+ articles, 1 000+ jurisprudences |

---

### 📞 Contact Commission

**HaqiTech Inc.**
- **Email :** contact@haqqi.ma
- **Site :** haqqi.ma (en cours)
- **Démo :** http://localhost:8002
- **Fondateur :** Al Walid Faouzi
- **Siège :** Dakhla, Maroc
