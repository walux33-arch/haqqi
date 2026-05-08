"""Generate PWA icons (PNG) from SVG source."""
import subprocess, os, tempfile

# Use cairosvg if available, otherwise create simple PNGs with PIL
try:
    from cairosvg import svg2png
    HAS_CAIRO = True
except ImportError:
    HAS_CAIRO = False

from PIL import Image, ImageDraw, ImageFont

ICONS_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "static", "icons")
os.makedirs(ICONS_DIR, exist_ok=True)


def make_png(size):
    path = os.path.join(ICONS_DIR, f"icon-{size}.png")
    if os.path.exists(path):
        return path
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Green circle
    r = size // 2 - 2
    cx, cy = size // 2, size // 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(21, 128, 61, 255))
    # White "ح" letter
    font_size = size // 2
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()
    # Center the text
    bbox = draw.textbbox((0, 0), "ح", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1]
    draw.text((tx, ty), "ح", fill=(255, 255, 255, 255), font=font)
    img.save(path, "PNG")
    print(f"Created {path}")
    return path


if __name__ == "__main__":
    for s in [48, 96, 144, 192, 512]:
        make_png(s)
    print("Done!")
