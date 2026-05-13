"""Management script for scrapers - run from command line or cron."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.ingestion.scrapers.adala import SCRAPERS


def run_all():
    for name, scraper in SCRAPERS.items():
        print(f"\n{'='*60}")
        print(f"Running: {scraper.label}")
        results = scraper.scrape_and_ingest(keyword="", max_items=5)
        print(f"  Total: {results['total']}, New: {results['new']}, Failed: {results['failed']}")
        for item in results["items"]:
            print(f"  ✓ {item['title'][:60]}")


def run_one(name: str, keyword: str = "", max_items: int = 10):
    if name not in SCRAPERS:
        print(f"Unknown scraper: {name}")
        print(f"Available: {', '.join(SCRAPERS.keys())}")
        return
    scraper = SCRAPERS[name]
    print(f"Running {scraper.label} with keyword='{keyword}'...")
    results = scraper.scrape_and_ingest(keyword=keyword, max_items=max_items)
    print(f"Results: {results['total']} found, {results['new']} new, {results['failed']} failed")
    for item in results["items"]:
        print(f"  ✓ {item['title'][:80]}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Haqi Legal Data Scrapers")
    parser.add_argument("scraper", nargs="?", default="all", help="Scraper name (adala, sgg, or 'all')")
    parser.add_argument("--keyword", "-k", default="", help="Search keyword")
    parser.add_argument("--max", "-m", type=int, default=10, help="Max items")
    args = parser.parse_args()

    if args.scraper == "all":
        run_all()
    else:
        run_one(args.scraper, args.keyword, args.max)
