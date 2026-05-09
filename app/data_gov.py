import httpx
import json
import os
import threading
import time

CKAN_BASE = "https://data.gov.ma/data/api/3/action"
CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "gov_cache.json")
CACHE_TTL = 3600  # 1 hour

_gov_cache = None
_gov_cache_time = 0
_lock = threading.Lock()


def _fetch_ckan(endpoint: str, params: dict = None) -> dict | None:
    try:
        r = httpx.get(f"{CKAN_BASE}/{endpoint}", params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("success"):
            return data["result"]
    except Exception as e:
        print(f"CKAN fetch error ({endpoint}): {e}")
    return None


def _categorize_dataset(name: str, notes_ar: str) -> list[str]:
    name_lower = name.lower()
    cats = []
    if "commercial" in name_lower or "commerce" in name_lower or "تجاري" in notes_ar:
        cats.append("تجاري")
    if "administratif" in name_lower or "administrative" in name_lower or "إداري" in notes_ar:
        cats.append("إداري")
    if "penal" in name_lower or "criminel" in name_lower or "جنائي" in notes_ar:
        cats.append("جنائي")
    if "civil" in name_lower or "مدني" in notes_ar:
        cats.append("مدني")
    if "famil" in name_lower or "أسرة" in notes_ar or "أسر" in notes_ar:
        cats.append("أسرة")
    if "appel" in name_lower or "استئناف" in notes_ar:
        cats.append("استئناف")
    if "generale" in name_lower or "general" in name_lower or "عام" in notes_ar:
        cats.append("عام")
    if "tribunal" in name_lower or "محكمة" in notes_ar or "محاكم" in notes_ar:
        cats.append("محاكم")
    if "annuaire" in name_lower or "دليل" in notes_ar:
        cats.append("دليل")
    if "evolution" in name_lower or "تطور" in notes_ar:
        cats.append("تطور")
    if not cats:
        cats.append("أخرى")
    return cats


def _extract_year(name: str, metadata_created: str) -> int | None:
    import re
    years = re.findall(r"\b(20\d{2})\b", name)
    if years:
        return max(int(y) for y in years)
    if metadata_created:
        return int(metadata_created[:4])
    return None


def fetch_gov_stats(force_refresh: bool = False) -> dict:
    global _gov_cache, _gov_cache_time
    now = time.time()
    if not force_refresh and _gov_cache is not None and (now - _gov_cache_time) < CACHE_TTL:
        return _gov_cache

    # Try file cache first
    if not force_refresh and os.path.isfile(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if (now - cached.get("_cached_at", 0)) < CACHE_TTL:
                _gov_cache = cached
                _gov_cache_time = cached.get("_cached_at", 0)
                return cached
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    result = {
        "_cached_at": now,
        "justice_group": {"total_datasets": 0, "title_ar": "العدل"},
        "by_year": {},
        "by_category": {},
        "recent_datasets": [],
        "summary": {
            "total_datasets": 0,
            "years_range": "",
            "categories_count": 0,
        }
    }

    # Fetch justice group
    group = _fetch_ckan("group_show", {"id": "justice"})
    if group:
        result["justice_group"]["total_datasets"] = group.get("package_count", 0)

    # Fetch datasets
    all_results = []
    for page in range(5):
        data = _fetch_ckan("package_search", {
            "q": "justice",
            "rows": 84,
            "start": page * 84,
        })
        if not data or not data.get("results"):
            break
        all_results.extend(data["results"])

    seen = set()
    for ds in all_results:
        ds_id = ds.get("id", "")
        if ds_id in seen:
            continue
        seen.add(ds_id)

        name = ds.get("name", "")
        notes_ar = ds.get("notes_ar", "") or ds.get("notes", "") or ""
        title_ar = ds.get("title_ar", "") or ds.get("title", "") or ""
        year = _extract_year(name, ds.get("metadata_created", ""))
        cats = _categorize_dataset(name, notes_ar)

        # Year
        if year:
            y_key = str(year)
            result["by_year"][y_key] = result["by_year"].get(y_key, 0) + 1

        # Category
        for c in cats:
            result["by_category"][c] = result["by_category"].get(c, 0) + 1

        # Recent (top 20)
        if len(result["recent_datasets"]) < 20:
            result["recent_datasets"].append({
                "id": ds_id,
                "title_ar": title_ar[:80],
                "notes_ar": notes_ar[:120],
                "year": year,
                "categories": cats,
                "url": f"https://data.gov.ma/data/ar/dataset/{ds_id}",
            })

    total = result["justice_group"]["total_datasets"] or len(seen)
    result["summary"] = {
        "total_datasets": total,
        "years_range": f"{min(map(int, result['by_year'].keys()))}-{max(map(int, result['by_year'].keys()))}" if result["by_year"] else "",
        "categories_count": len(result["by_category"]),
    }

    # Cache to file
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

    _gov_cache = result
    _gov_cache_time = now
    return result


def fetch_and_cache_async():
    threading.Thread(target=fetch_gov_stats, daemon=True).start()


# Warm cache on import
fetch_and_cache_async()
