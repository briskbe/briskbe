#!/usr/bin/env python3
"""Scrape products from all brand subcategories under
https://www.uitlaataanbiedingen.nl/uitlaatset/ into a CSV."""
import csv
import re
import time
import urllib.request

BASE = "https://www.uitlaataanbiedingen.nl/uitlaatset/"
UA = "Mozilla/5.0 (compatible; UitlaatScraper/1.0)"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def get_brand_urls(html):
    pat = re.compile(r'href="(https://www\.uitlaataanbiedingen\.nl/uitlaatset/[^"/]+/)"')
    return sorted(set(pat.findall(html)))


PRODUCT_BLOCK = re.compile(
    r'<div class="product col-xs-6[^"]*">(.*?)<div class="info">(.*?)</div>\s*</div>',
    re.DOTALL,
)


def parse_products(html, brand_url):
    products = []
    # Split on product card opener
    chunks = html.split('<div class="product col-xs-')
    for chunk in chunks[1:]:
        # Card spans until next product or end of products container
        card = chunk
        # First anchor inside image-wrap holds url + title (brand + name)
        m_link = re.search(
            r'<div class="image-wrap">\s*<a href="([^"]+)" title="([^"]*)"',
            card,
        )
        if not m_link:
            continue
        url = m_link.group(1)
        title_attr = m_link.group(2)
        # Brand is first word of title attr (e.g., "Topautoparts ...", "Edex ...")
        brand_name = title_attr.split(" ", 1)[0] if title_attr else ""
        full_title = title_attr

        m_img = re.search(r'<img src="([^"]+)"', card)
        image = m_img.group(1) if m_img else ""

        m_desc = re.search(r'<div class="text">\s*(.*?)\s*</div>', card, re.DOTALL)
        desc = re.sub(r"\s+", " ", m_desc.group(1)).strip() if m_desc else ""

        m_title = re.search(
            r'class="title">\s*(.*?)\s*</a>', card, re.DOTALL
        )
        short_title = re.sub(r"\s+", " ", m_title.group(1)).strip() if m_title else full_title

        m_old = re.search(r'class="old-price">([^<]+)</span>', card)
        old_price = m_old.group(1).strip() if m_old else ""

        # Current price: inside info block, after the title <a>. Sale layout has
        # it inside <div class="right">; non-sale shows it as bare text. Strip
        # the old-price span first so we don't capture it.
        info_text = re.sub(r'<span class="old-price">[^<]*</span>', "", card)
        m_new = re.search(
            r'class="title">.*?</a>(.*?)</div>\s*</div>\s*(?:</div>)?',
            info_text,
            re.DOTALL,
        )
        price = ""
        if m_new:
            mp = re.search(r"€[\s]*[0-9][0-9.,]*", m_new.group(1))
            if mp:
                price = mp.group(0).replace(" ", "")

        products.append(
            {
                "category_url": brand_url,
                "brand_subcategory": brand_url.rstrip("/").rsplit("/", 1)[-1],
                "manufacturer": brand_name,
                "title": short_title,
                "full_title": full_title,
                "price": price,
                "old_price": old_price,
                "url": url,
                "image": image,
                "description": desc,
            }
        )
    return products


def main():
    print("Fetching root category...")
    root = fetch(BASE)
    brands = [u for u in get_brand_urls(root) if u != BASE]
    print(f"Found {len(brands)} brand subcategories")

    all_products = []
    seen = set()
    for i, b in enumerate(brands, 1):
        print(f"[{i}/{len(brands)}] {b}")
        try:
            html = fetch(b)
        except Exception as e:
            print(f"  ! error: {e}")
            continue
        prods = parse_products(html, b)
        print(f"  -> {len(prods)} products")
        for p in prods:
            if p["url"] in seen:
                continue
            seen.add(p["url"])
            all_products.append(p)
        time.sleep(0.5)

    out = "uitlaatset_products.csv"
    fields = [
        "category_url",
        "brand_subcategory",
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
        for p in all_products:
            w.writerow(p)
    print(f"Wrote {len(all_products)} unique products to {out}")


if __name__ == "__main__":
    main()
