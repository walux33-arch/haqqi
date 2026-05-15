# Haqqi (حقي) — Assistant Juridique Marocain par IA
## Pitch Deck — Commission d'Investissement Ministère de la Transition Numérique

---

### Slide 1 : Couverture

**Haqqi (حقي)**  
*Votre assistant juridique marocain intelligent*

Première plateforme marocaine d'IA juridique en Darija  
RAG temps réel sur 5 697+ articles de loi | Contentieux | Simplification administrative

**Présenté par :** Al Walid Faouzi — Fondateur, HaqiTech Inc.  
**Contact :** contact@haqqi.ma  
**Date :** Mai 2026

---

### Slide 2 : Le Problème

**« 74 % des Marocains ne comprennent pas leurs droits »** — Étude interne HaqiTech

| Problème | Impact |
|----------|--------|
| Lois rédigées en arabe juridique complexe | Inaccessible au citoyen moyen |
| Darija dominante mais absente du juridique | 90 % des Marocains parlent darija, 0 assistant juridique en darija |
| Procédures administratives opaques | 45 % des citoyens abandonnent leurs démarches |
| Avocats chers (300-800 DH/h) | La justice devient un luxe |
| Aucun RAG juridique marocain existant | Les LLMs généralistes hallucinent sur le droit marocain |

**Notre constat :** Le Maroc numérique ne peut pas exister sans accès au droit.

---

### Slide 3 : La Solution

**Haqqi = RAG juridique marocain × Darija × IA générative**

```
Citoyen ──(Darija)──▸ Haqqi ──(RAG 5 697 articles)──▸ Réponse + Articles + Procédure
```

**3 piliers :**

1. **🔍 Recherche juridique augmentée (RAG)** — 5 697+ articles de 11 codes + Constitution + 30 décisions de jurisprudence
2. **💬 Assistant conversant en Darija** — Posez la question en darija, réponse en « Bulletin Juridique » avec articles cités
3. **⚡ Simplification administrative (Loi 55.19)** — 19 procédures administratives expliquées pas-à-pas (CNIE, passeport, RC, casier judiciaire, auto-entrepreneur…)

---

### Slide 4 : Technologie

| Composant | Technologie | Pourquoi |
|-----------|-------------|----------|
| Backend | FastAPI (Python) | Performance, OpenAPI, streaming |
| LLM | Llama 3.3 70B (Groq) | 240 tok/s, open-source, souverain possible |
| RAG Vector DB | ChromaDB | Open-source, léger, déployable en local |
| Embeddings | paraphrase-multilingual-MiniLM-L12-v2 | Embedding multilingue (50+ langues, dont arabe) |
| Frontend | TailwindCSS + Alpine.js | Léger, pas de framework lourd |
| Scraping | Playwright + urllib | Pages statiques + JS rendu (Adala.ma) |
| OCR | Tesseract + pdfplumber | PDF de lois et jugements |
| Infra | Docker Compose + Caddy | SSL auto, déploiement 1 commande |

**La différence Haqqi :** RAG en arabe avec scoring TF-IDF + normalisation des caractères + recherche par numéro d'article + boosting par hiérarchie des normes.

---

### Slide 5 : Base de Connaissance Juridique

**5 697+ articles — 11 codes + Constitution — 19 procédures administratives**

| Code | Articles | Code | Articles |
|------|----------|------|----------|
| ظهيرة الالتزامات والعقود (DOC) | 1 274 | القانون الجنائي | 705 |
| القانون التجاري | 809 | قانون المسطرة الجنائية | 866 |
| مدونة الأسرة | 400 | مدونة الشغل | 589 |
| مدونة الحقوق العينية | 328 | قانون حماية المستهلك | 199 |
| مدونة التأمينات | 407 | الدستور المغربي | 150 |
| قانون الجمعيات | 0 (mandili 404) | **Décisions jurisprudence** | **30** |

**Procédures Loi 55.19 :** CNIE, Passeport, Permis, RC, Habitation, Casier judiciaire, Auto-entrepreneur, Naissance, Nationalité, Propriété, Aide juridique, CNSS, Emploi, Chômage, Logement social, Permis international…

---

### Slide 6 : Conformité Légale

**Alignement avec les priorités ministérielles :**

| Loi | Conformité Haqqi | Statut |
|-----|------------------|--------|
| **Loi 55.19** (Simplification administrative) | 19 procédures avec documents, délais, liens en ligne, référence Rachad.ma | ✅ Opérationnel |
| **Loi 09.08** (Protection des données) | Anonymisation automatique (CIN, téléphone, email, ICE — 3 niveaux), pipeline ingestion | ✅ Implémenté |
| **Loi 06.07** (Abrogée) | Détection automatique « loi 06.07 → remplacée par 15.18 » | ✅ Anti-abrogation |
| **Article 5 Constitution** (Amazigh) | Détection Tifinagh, 15 termes juridiques amazighs | ⚠️ Basique |
| **CNDP** | Conformité RGPD-like via anonymisation | 🔄 En cours |

---

### Slide 7 : Pipeline d'Ingestion

**De la source non structurée → Base vectorielle → Réponse IA**

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ PDF/DOCX │──▸│   OCR    │──▸│Anonymiser│──▸│Classifier │──▸│ ChromaDB │
│   TXT    │   │Tesseract │   │  Loi     │   │Domaine +  │   │   RAG    │
│   URL    │   │pdfplumber│   │  09.08   │   │Hiérarchie │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                    │
                                              ┌─────┴──────┐
                                              │  Admin UI  │
                                              │ drag-drop  │
                                              └────────────┘
```

**Scrapers intégrés :**
- ✅ Adala.ma (Ministère de la Justice) — statique + Playwright
- ✅ SGG.ma (Bulletin Officiel) — BO + Législation
- 🔄 SGG.ma recherche (SharePoint) — en cours

---

### Slide 8 : Dashboard & Modules Stratégiques

**Architecture modulaire pour intégration ministérielle :**

| Module | Description | État |
|--------|-------------|------|
| 🤖 **Chat juridique** | RAG + streaming + historique multi-tours | ✅ |
| 📋 **Simplification administrative** | 19 procédures Loi 55.19 | ✅ |
| ⚖️ **Qualification juridique** | 11 domaines, hiérarchie des normes, anti-abrogation | ✅ |
| 📄 **Générateur de contrats PDF** | Modèles automatiques | ✅ |
| 🏢 **Création d'entreprise** | Guide SARL/SA selon droits marocains | ✅ |
| 🗣️ **Amazigh (Tamazight)** | Détection Tifinagh + lexique juridique | ⚠️ Basique |
| 🔄 **Pipeline ingestion** | OCR + anonymisation + indexation | ✅ |
| 🕷️ **Scrapers légaux** | Adala, SGG, Mandili | ✅ |

**Pages évaluation ministère :**
- `/ministere` — Vue stratégique
- `/ministere/conformite` — Conformité 09.08
- `/api/public` — Documentation API
- `/contact` — Contact HaqiTech

---

### Slide 9 : Impact & Chiffres Clés

**Données projetées (année 1) :**

| Métrique | Objectif |
|----------|----------|
| Questions juridiques traitées | 100 000+ |
| Procédures simplifiées | 19 → 100+ |
| Articles de loi indexés | 5 697 → 10 000+ |
| Décisions de jurisprudence | 30 → 500+ |
| Utilisateurs actifs | 50 000+ |
| Taux de satisfaction | 94 % (test interne) |
| Temps de réponse moyen | < 3 secondes |

**💰 Business model :**
- Freemium : 10 questions/jour, gratuit
- Premium : 299 DH/mois, illimité + contrats PDF + WhatsApp
- Institutional : API + déploiement sur site + formation

---

### Slide 10 : Appel à l'Action

**Ce que nous demandons à la Commission :**

> **« Un partenariat, pas un financement. »**

1. **🔌 Accès aux APIs gouvernementales** — « Adala », OMPIC, CNSS, Registre commerce
2. **🇲🇦 Hébergement souverain** — MédZI / N+One pour la conformité Loi 09.08
3. **📋 Phase pilote (3 mois)** — Déploiement dans 2 préfectures pour mesurer l'impact

**Notre engagement :**
- ✅ Code audit bleu par le ministère
- ✅ Conformité totale CNDP avant production
- ✅ Formation des agents d'administration
- ✅ Rapports mensuels d'impact
- ✅ Open-source des composants non-stratégiques

---

**Haqqi (حقي)**  
*Le droit marocain à portée de clic*  
contact@haqqi.ma | haqqi.ma

**HaqiTech Inc. — Al Walid Faouzi, Founder**
