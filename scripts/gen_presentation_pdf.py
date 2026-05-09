import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fpdf import FPDF

FONT_PATH = r"C:\Windows\Fonts\Arial.ttf"

class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 5, "Haqqi — Guide de presentation", align="C")
            self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def _rx(self):
        self.set_x(self.l_margin)

    def title_page(self):
        self.add_font("Arial", "", FONT_PATH)
        self.add_font("Arial", "B", FONT_PATH)
        self.ln(50)
        self.set_font("Arial", "B", 36)
        self.set_text_color(21, 128, 61)
        self.cell(0, 15, "Haqqi", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Arial", "", 18)
        self.set_text_color(60, 60, 60)
        self.cell(0, 12, "Guide de presentation", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 12, "Devant les comites de financement", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)
        self.set_font("Arial", "", 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Walid Faouzi", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 8, "2026", align="C", new_x="LMARGIN", new_y="NEXT")

    def sec(self, num, title):
        self._rx()
        self.set_font("Arial", "B", 15)
        self.set_text_color(21, 128, 61)
        self.ln(3)
        self.cell(0, 10, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(21, 128, 61)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def sub(self, title):
        self._rx()
        self.set_font("Arial", "B", 12)
        self.set_text_color(50, 50, 50)
        self.ln(2)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def txt(self, text):
        self._rx()
        self.set_font("Arial", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, text)
        self.ln(1)

    def bul(self, text):
        self._rx()
        self.set_font("Arial", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, "  -  " + text)

    def code(self, text):
        self._rx()
        self.set_fill_color(240, 240, 240)
        self.set_font("Courier", "", 8)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5, text, fill=True)
        self._rx()
        self.ln(2)

    def qa(self, q, a):
        self._rx()
        self.set_font("Arial", "B", 10)
        self.set_text_color(21, 128, 61)
        self.cell(0, 6, "Q: " + q, new_x="LMARGIN", new_y="NEXT")
        self._rx()
        self.set_font("Arial", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, a)
        self.ln(2)

    def table_header(self, cols):
        self._rx()
        self.set_font("Arial", "B", 9)
        self.set_fill_color(230, 245, 230)
        for w, c in cols:
            self.cell(w, 8, c, border=1, align="C", fill=True)
        self.ln()

    def table_row(self, cols):
        self._rx()
        self.set_font("Arial", "", 9)
        for w, c in cols:
            self.cell(w, 7, c, border=1, align="C")
        self.ln()


pdf = PDF("P", "mm", "A4")
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()
pdf.title_page()

# ===== 1 =====
pdf.add_page()
pdf.sec("1", "Preparation avant la presentation")
pdf.sub("Equipement")
pdf.txt("Batterie 100% • Fermer tous les logiciels (Teams, notifications) • Bureau propre")
pdf.sub("Lancer le serveur (PowerShell)")
pdf.code('cd C:\\Users\\Laptop\\Desktop\\haqqi\n$env:PYTHONIOENCODING="utf-8"\npython -m uvicorn app.main:app --reload --port 8000')
pdf.txt("Ouvrir http://localhost:8000 dans le navigateur")
pdf.sub("Test rapide avant la presentation")
pdf.bul('Chat: "شنو هو الطلاق فالمغرب؟" — verifier le streaming')
pdf.bul("Ouvrir /contracts — verifier generation PDF")
pdf.bul("Ouvrir /admin — verifier les stats")
pdf.bul("Ouvrir /pitch — verifier les slides")

# ===== 2 =====
pdf.add_page()
pdf.sec("2", "Deroulement (15 minutes)")
pdf.txt("Total: 15 min = 5 min de demo + 10 min de questions")
pdf.table_header([(30, "Temps"), (40, "Section"), (120, "Contenu")])
for r in [
    ("0:00-0:30", "Intro", "Presentation de Haqqi"),
    ("0:30-3:00", "Pitch Deck", "Probleme → Solution → Marche → Techno → Chiffres"),
    ("3:00-5:00", "Demo", "Chat → Contrats → Societes → Jurisprudence → Admin"),
    ("5:00-15:00", "Questions", "Q&A"),
]:
    pdf.table_row([(30, r[0]), (40, r[1]), (120, r[2])])

# ===== 3 =====
pdf.add_page()
pdf.sec("3", "Script complet")
pdf.sub("Introduction (30s)")
pdf.txt("Bonjour, je suis Walid Faouzi, developpeur marocain. Haqqi est le premier assistant juridique marocain par intelligence artificielle qui repond aux questions juridiques en darija. Voyons le probleme que nous avons cherche a resoudre.")

pdf.sub("Pitch Deck — slides sur /pitch")
for s, d in [
    ("01 Cover", "Haqqi — Your AI Moroccan Legal Assistant"),
    ("02 Problem", "80% des Marocains parlent darija mais les lois sont en fusha/francais"),
    ("03 Solution", "Haqqi repond en darija + contrats PDF + societes + jurisprudence"),
    ("04 Market", "37M Marocains ont besoin d'info juridique. 0 concurrent en darija"),
    ("05 Tech", "Pipeline RAG: ChromaDB ← Supabase ← JSON"),
    ("06 Data", "3,777 articles de 5 codes + 83 datasets gouvernementaux"),
    ("07 Traction", "Construit en 5 semaines, 57 fichiers, 18,000 lignes de code"),
    ("08 Business", "Free ← $9/mo ← Enterprise $499/mo. MRR $14k/mo"),
    ("09 Competition", "Aucun concurrent ne repond en darija"),
    ("10 Demo", "Demonstration en direct"),
    ("11 Roadmap", "Q2 2026: WhatsApp Bot + Code de la route"),
    ("12 Team", "Solo founder"),
    ("13 Ask", "$50k pour 12% — 18 mois de runway"),
]:
    pdf._rx()
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(21, 128, 61)
    pdf.cell(0, 6, s, new_x="LMARGIN", new_y="NEXT")
    pdf._rx()
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 6, d)
    pdf.ln(1)

# ===== 4 =====
pdf.add_page()
pdf.sec("4", "Demo en direct (2 minutes)")
pdf.sub("1. Chat en darija (30s)")
pdf.txt('Taper: "شنو هي شروط الزواج فالمغرب؟"')
pdf.bul("Montrer le streaming mot par mot")
pdf.bul("Montrer la source (article X du code de la famille)")
pdf.txt('Dire: "Cette reponse n est pas sur ChatGPT. Haqqi a 3,777 articles juridiques marocains."')

pdf.sub("2. Jurisprudence (15s)")
pdf.txt("Ouvrir /judgements • Filtrer par chambre civile")
pdf.txt("Dire: 30 arrets de la Cour de Cassation")

pdf.sub("3. Creation de societe (15s)")
pdf.txt("Ouvrir /incorporation • Cliquer sur SARL • Montrer les details")

pdf.sub("4. Contrats PDF (20s)")
pdf.txt("Ouvrir /contracts • Choisir contrat de location")
pdf.txt("Remplir les champs et generer le PDF")
pdf.txt("Dire: contrat pret a signer, disponible en 3 formats")

pdf.sub("5. Admin Dashboard (10s)")
pdf.txt("Ouvrir /admin • Montrer les stats: 3,777 articles, 5 codes, 83 datasets")
pdf.txt("Dire: Ces chiffres sont en temps reel")

# ===== 5 =====
pdf.add_page()
pdf.sec("5", "Questions techniques anticipees")
pdf.qa("Quelle est la difference avec ChatGPT?",
       "ChatGPT a une base de donnees generale. Haqqi utilise du RAG specialise sur les lois marocaines. Il repond avec l'article et le code exact. Et il y a un mode demo gratuit sans carte bancaire.")
pdf.qa("Comment garantir que l'IA ne se trompe pas?",
       "3 niveaux: 1) RAG recupere la source depuis les codes juridiques 2) L'IA repond seulement sur les infos dans le contexte 3) temperature=0.3 = peu de creativite, fidele a la source")
pdf.qa("Quel est le stack technique?",
       "Python + FastAPI (backend). ChromaDB + Supabase (vector search). Groq Llama 3.3 70B (LLM). Tailwind CSS (frontend). Docker + GitHub Actions (DevOps).")
pdf.qa("Quelle est la source des lois?",
       "5 codes officiels: Penal (705) • Obligations et Contrats (1,274) • Commercial (809) • Famille (400) • Travail (589) + 83 datasets de data.gov.ma + 30 arrets de la Cour de Cassation")
pdf.qa("Avez-vous teste avec des utilisateurs?",
       "Pas encore officiellement. Mais le mode demo fonctionne sans API key. Pret a lancer en 3 jours.")
pdf.qa("Quel est le business plan?",
       "Free (10 requetes/jour) ← Pro $9/mois (illimite + PDF) ← Enterprise $499/mois (API + WhatsApp). Objectif: 1,000 Pro + 10 Enterprise = $14k/mois.")

# ===== 6 =====
pdf.add_page()
pdf.sec("6", "Conseils importants")
pdf.sub("A ne PAS dire:")
pdf.bul('"Ce n est qu un MVP avec des bugs" → Dire: "C est la version 1 avec des ameliorations continues"')
pdf.bul('"Je n ai pas d argent" → Dire: "Construit a cout zero, maintenant on a besoin de grandir"')

pdf.sub("Pieges a eviter:")
pdf.bul("Ne pas ouvrir trop de tabs dans le navigateur")
pdf.bul("Desactiver les notifications Windows")
pdf.bul("Ne pas rester silencieux en changeant de slide")

pdf.sub("3 points cles:")
pdf._rx()
pdf.set_font("Arial", "B", 11)
pdf.set_text_color(21, 128, 61)
pdf.cell(0, 8, "1. Darija-first — aucun concurrent", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "2. Zero budget — capital-efficient des le jour 1", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "3. Donnees reelles — 3,777 articles des codes officiels", new_x="LMARGIN", new_y="NEXT")

# ===== 7 =====
pdf.add_page()
pdf.sec("7", "Plan B (backup)")
pdf.table_header([(60, "Probleme"), (130, "Solution")])
for p, s in [
    ("Serveur plante", "python -m uvicorn ... = 3 secondes"),
    ("Chat ne repond pas", '"C est le mode demo, la version complete utilise Groq API"'),
    ("PDF ne se telecharge pas", '"Essayez depuis chez vous, probablement la securite du navigateur"'),
    ("Stats non affichees", '"Statistiques en direct depuis la base de donnees"'),
    ("Pas d internet", "Ouvrir le pitch deck (version PDF de secours)"),
]:
    pdf.table_row([(60, p), (130, s)])

# ===== 8 =====
pdf.ln(10)
pdf.sec("8", "Conclusion (30 secondes)")
pdf.txt("Haqqi est la premiere plateforme juridique marocaine en darija. Construite en 5 semaines sans budget. Aujourd'hui: 3,777 articles, 30 arrets, contrats PDF. Besoin de $50k pour finaliser le WhatsApp bot, ajouter le code de la route, et lancer officiellement. Merci de votre attention.")

output = os.path.join(os.path.dirname(__file__), "..", "presentation_guide.pdf")
pdf.output(output)
print("OK:", output)
