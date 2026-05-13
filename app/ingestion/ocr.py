"""Text extraction from PDFs, images, and documents."""

import os
import re
import tempfile


def extract_from_pdf(filepath: str) -> str:
    """Extract text from PDF. Uses pdfplumber for text-based PDFs."""
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
        if text.strip():
            return text.strip()
    except ImportError:
        pass
    except Exception as e:
        print(f"pdfplumber error: {e}")

    # Fallback: try PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        for page in reader.pages:
            text += page.extract_text() or ""
        if text.strip():
            return text.strip()
    except ImportError:
        pass
    except Exception as e:
        print(f"PyPDF2 error: {e}")

    # Fallback: try OCR via pytesseract
    return _ocr_fallback(filepath)


def _ocr_fallback(filepath: str) -> str:
    """OCR fallback for scanned documents."""
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        return ""

    try:
        if filepath.lower().endswith(".pdf"):
            from pdf2image import convert_from_path
            images = convert_from_path(filepath, dpi=300)
            text = ""
            for img in images:
                text += pytesseract.image_to_string(img, lang="ara+fra") + "\n"
            return text.strip()
        else:
            img = Image.open(filepath)
            return pytesseract.image_to_string(img, lang="ara+fra").strip()
    except Exception as e:
        print(f"OCR error: {e}")
        return ""


def extract_from_image(filepath: str) -> str:
    """Extract text from image via OCR."""
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(filepath)
        return pytesseract.image_to_string(img, lang="ara+fra").strip()
    except ImportError:
        return ""
    except Exception as e:
        print(f"Image OCR error: {e}")
        return ""


def extract_text(filepath: str) -> str:
    """Detect file type and extract text."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return extract_from_pdf(filepath)
    elif ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
        return extract_from_image(filepath)
    elif ext in (".txt", ".md", ".html", ".xml"):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    elif ext == ".docx":
        try:
            import docx
            doc = docx.Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            return ""
        except Exception as e:
            print(f"DOCX error: {e}")
            return ""
    return ""
