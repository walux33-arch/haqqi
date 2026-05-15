"""Simple PDF generator - no fpdf2 complex layout issues."""
import sys
sys.stdout = open(1, 'w', encoding='utf-8', closefd=False)

import os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

try:
    from fpdf import FPDF
except ImportError:
    os.system("pip install fpdf2")
    from fpdf import FPDF

# Find font
FONT_PATH = None
# Prefer DejaVuSans for better Unicode coverage
for f in [
    "C:/Windows/Fonts/DejaVuSans.ttf",
    os.path.join(BASE, "data", "fonts", "DejaVuSans.ttf"),
    "C:/Windows/Fonts/arial.ttf",
]:
    if os.path.exists(f):
        FONT_PATH = f.replace("\\", "/")
        break

if not FONT_PATH:
    import urllib.request
    os.makedirs(os.path.join(BASE, "data", "fonts"), exist_ok=True)
    url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
    path = os.path.join(BASE, "data", "fonts", "DejaVuSans.ttf").replace("\\", "/")
    urllib.request.urlretrieve(url, path)
    FONT_PATH = path

bold_path = FONT_PATH.replace("Sans.ttf", "Sans-Bold.ttf")
italic_path = FONT_PATH.replace("Sans.ttf", "Sans-Oblique.ttf")
mono_path = FONT_PATH.replace("Sans.ttf", "SansMono.ttf")

for url, local in [
    ("https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf", bold_path),
    ("https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Oblique.ttf", italic_path),
    ("https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSansMono.ttf", mono_path),
]:
    if not os.path.exists(local):
        try:
            import urllib.request
            urllib.request.urlretrieve(url, local)
        except:
            pass


def text_to_pdf(text, pdf_path, title=""):
    pdf = FPDF()
    pdf.add_font("DJS", "", FONT_PATH)
    if os.path.exists(bold_path):
        pdf.add_font("DJS", "B", bold_path)
    if os.path.exists(italic_path):
        pdf.add_font("DJS", "I", italic_path)
    if os.path.exists(mono_path):
        pdf.add_font("DJM", "", mono_path)
    else:
        pdf.add_font("DJM", "", FONT_PATH)

    pdf.add_page()
    lines = text.split("\n")

    for line in lines:
        s = line.strip()
        if not s:
            pdf.ln(3)
            continue

        # Skip horizontal rules
        if re.match(r'^[-*=_]{3,}$', s):
            pdf.ln(2)
            continue

        # Headings
        if s.startswith("# "):
            pdf.set_font("DJS", "B", 16)
            pdf.set_text_color(21, 128, 61)
            pdf.multi_cell(0, 8, s[2:], new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(21, 128, 61)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)
        elif s.startswith("## "):
            pdf.set_font("DJS", "B", 12)
            pdf.set_text_color(22, 101, 52)
            pdf.multi_cell(0, 7, s[3:], new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(200, 200, 200)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(2)
        elif s.startswith("### "):
            pdf.set_font("DJS", "B", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 6, s[4:], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif s.startswith("#### "):
            pdf.set_font("DJS", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 5, s[5:], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif s.startswith("- ") or s.startswith("* "):
            pdf.set_font("DJS", "", 9)
            pdf.set_text_color(26, 26, 46)
            text = s[2:]
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'`(.+?)`', r'"\1"', text)
            pdf.multi_cell(0, 5, "  -  " + text, new_x="LMARGIN", new_y="NEXT")
        elif s.startswith("|"):
            # Skip table rows (too complex for simple PDF)
            pass
        elif s.startswith("```"):
            # Skip code block markers
            pass
        else:
            # Normal paragraph
            pdf.set_font("DJS", "", 9)
            pdf.set_text_color(26, 26, 46)
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
            text = re.sub(r'`(.+?)`', r'"\1"', text)
            # Remove special characters that might cause issues
            text = text.replace("•", "-").replace("│", "|")
            pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")

    pdf.output(pdf_path)
    return pdf.pages_count


if __name__ == "__main__":
    files = [
        ("pitch_deck_fr.md", "Haqqi_Pitch_Deck.pdf"),
        ("fiche_technique_fr.md", "Haqqi_Fiche_Technique.pdf"),
        ("demo_script_fr.md", "Haqqi_Demo_Script.pdf"),
    ]
    for src, dst in files:
        src_path = os.path.join(DATA, src)
        dst_path = os.path.join(DATA, dst)
        if os.path.exists(src_path):
            with open(src_path, "r", encoding="utf-8") as f:
                text = f.read()
            pages = text_to_pdf(text, dst_path)
            print(f"OK {dst} ({pages} pages)")

    print(f"\nPDFs: {DATA}")
