#!/usr/bin/env python3
"""Scrape products from all subcategories of
https://www.uitlaataanbiedingen.nl/universele-uitlaatdelen/ into a CSV.

Reuses the parser from scrape.py."""
import csv
import re
import time

from scrape import fetch, parse_products

BASE = "https://www.uitlaataanbiedingen.nl/universele-uitlaatdelen/"


def get_subcats(html):
    pat = re.compile(
        r'href="(https://www\.uitlaataanbiedingen\.nl/universele-uitlaatdelen/[^"/]+/)"'
    )
    return sorted(set(pat.findall(html)))


def main():
    print("Fetching root category...")
    root = fetch(BASE)
    subs = get_subcats(root)
    # Also scrape root in case some products live directly there.
    targets = [BASE] + [s for s in subs if s != BASE]
    print(f"Targets: {len(targets)}")

    seen = set()
    rows = []
    for i, url in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] {url}")
        try:
            html = fetch(url)
        except Exception as e:
            print(f"  ! error: {e}")
            continue
        prods = parse_products(html, url)
        print(f"  -> {len(prods)} products")
        for p in prods:
            if p["url"] in seen:
                continue
            seen.add(p["url"])
            # Rename brand_subcategory -> subcategory for clarity
            p["subcategory"] = p.pop("brand_subcategory")
            rows.append(p)
        time.sleep(0.5)

    out = "universele_uitlaatdelen_products.csv"
    fields = [
        "category_url",
        "subcategory",
        "manufacturer",
        "title",
        "full_title",
        "price",
        "old_price",
        "url",
        "image",
        "description",
    ]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        for p in rows:
            w.writerow({k: p.get(k, "") for k in fields})
    print(f"Wrote {len(rows)} unique products to {out}")


if __name__ == "__main__":
    main()
