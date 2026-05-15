import json, os

data_dir = os.path.join(os.path.dirname(__file__), "data", "laws")
for fname in sorted(os.listdir(data_dir)):
    if not fname.endswith(".json"):
        continue
    fpath = os.path.join(data_dir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    articles = data.get("articles", [])
    print(f"{fname}: {len(articles)} articles, keys={list(data.keys())}")
    if articles:
        a = articles[0]
        print(f"  first article keys: {list(a.keys())}")
        print(f"  number={a.get('number','?')}, content len={len(a.get('content',''))}")
