import urllib.request, os

font_path = os.path.join(os.path.dirname(__file__), "..", "fonts", "DejaVuSans.ttf")
os.makedirs(os.path.dirname(font_path), exist_ok=True)

if not os.path.exists(font_path):
    print("Downloading DejaVuSans.ttf...")
    urllib.request.urlretrieve(
        "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf",
        font_path,
    )
    print("Downloaded!")
else:
    print("Font already exists")

print("Font path:", font_path)
