#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crawler — Résidences services seniors (PACA + Auvergne-Rhône-Alpes).

Source backbone : sanitaire-social.com (annuaire server-rendered, exhaustif).
Moteur          : OBSCURA (headless browser, h4ckf0r0day/obscura v0.1.7).
Stages          :
  list     -> data/raw/master_list.json   (nom, adresse, fiche_url, dept, region)
  geocode  -> data/raw/geocoded.json       (+ lat, lng via BAN api-adresse.data.gouv.fr)
  detail   -> data/raw/details.json        (+ phone, website, photo, price, surface, desc)
Usage : python crawl/crawl.py <stage>
"""
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

OBS_DIR = Path("C:/Users/PGNK2128/Downloads/tools/obscura")
OBS = str(OBS_DIR / "obscura.exe")
ENV = os.environ.copy()
ENV["PATH"] = str(OBS_DIR) + os.pathsep + ENV.get("PATH", "")

BASE = ("https://www.sanitaire-social.com/annuaire-ehpad-maisons-de-retraite/"
        "residences-seniors/liste-")

# 18 départements en scope : slug sanitaire-social -> (code, region)
DEPTS = {
    "alpes-de-haute-provence-04": ("04", "PACA"),
    "hautes-alpes-05": ("05", "PACA"),
    "alpes-maritimes-06": ("06", "PACA"),
    "bouches-du-rhone-13": ("13", "PACA"),
    "var-83": ("83", "PACA"),
    "vaucluse-84": ("84", "PACA"),
    "ain-01": ("01", "ARA"),
    "allier-03": ("03", "ARA"),
    "ardeche-07": ("07", "ARA"),
    "cantal-15": ("15", "ARA"),
    "drome-26": ("26", "ARA"),
    "isere-38": ("38", "ARA"),
    "loire-42": ("42", "ARA"),
    "haute-loire-43": ("43", "ARA"),
    "puy-de-dome-63": ("63", "ARA"),
    "rhone-69": ("69", "ARA"),
    "savoie-73": ("73", "ARA"),
    "haute-savoie-74": ("74", "ARA"),
}
PER_PAGE = 25
EVAL_LIST = (Path(__file__).parent / "extract_list.js").read_text(encoding="utf-8")
EVAL_DETAIL = (Path(__file__).parent / "extract_detail.js").read_text(encoding="utf-8")
EVAL_ENRICH = (Path(__file__).parent / "extract_enrich.js").read_text(encoding="utf-8")
EVAL_DEEP = (Path(__file__).parent / "extract_deep.js").read_text(encoding="utf-8")

# Détection d'opérateur à partir du nom (substring, insensible à la casse).
OPERATORS = [
    ("domitys", "Domitys"),
    ("senioriales", "Les Senioriales"),
    ("arcadie", "Les Jardins d'Arcadie"),
    ("ovelia", "Ovelia"),
    ("cogedim", "Cogedim Club"),
    ("girandi", "Les Girandières"),
    ("villavie", "Villavie"),
    ("heurus", "Heurus"),
    ("nohee", "Nohée"),
    ("nohée", "Nohée"),
    ("espace et vie", "Espace & Vie"),
    ("espace & vie", "Espace & Vie"),
    ("steva", "Steva"),
    ("happy senior", "Happy Senior"),
    ("colis", "Colisée"),
    ("templitudes", "Les Templitudes"),
    ("emera", "Emera"),
    ("hesperides", "Les Hespérides"),
    ("hespérides", "Les Hespérides"),
    ("zenitude", "Zénitude"),
    ("montana", "Résidence Montana"),
    ("oh activ", "Oh Activ"),
    ("obeo", "OBEO Résidences"),
    ("les essentielles", "Les Essentielles"),
    ("sairenor", "Sairenor"),
    ("jardins de cybele", "Jardins de Cybèle"),
    ("jardins de cybèle", "Jardins de Cybèle"),
    ("aegide", "Domitys"),
]


def detect_operator(name):
    low = (name or "").lower()
    for sub, canon in OPERATORS:
        if sub in low:
            return canon
    return "Indépendant / autre"


def obscura_scrape(urls, eval_js, concurrency=6, timeout=60):
    """Run `obscura scrape` over urls with a JS eval. Returns dict url -> eval-string (or None)."""
    if not urls:
        return {}
    cmd = [OBS, "scrape", *urls, "-e", eval_js, "--format", "json",
           "--concurrency", str(concurrency), "--timeout", str(timeout), "--quiet"]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=ENV,
                          encoding="utf-8", errors="replace")
    out = proc.stdout.strip()
    start = out.find("{")
    if start < 0:
        print(f"  ! no JSON in output. stderr tail: {proc.stderr[-300:]}")
        return {}
    data = json.loads(out[start:])
    res = {}
    for r in data.get("results", []):
        if "eval" in r:
            res[r["url"]] = r["eval"]
        else:
            print(f"  ! {r.get('url','?')[-40:]} -> {r.get('error')}")
            res[r["url"]] = None
    return res


def url_for(slug, page=1):
    return f"{BASE}{slug}" + (f"?page={page}" if page > 1 else "")


def stage_list():
    print("== STAGE list ==")
    # Pass 1 : page 1 of every department, capture count + cards.
    p1 = {url_for(s): s for s in DEPTS}
    print(f"Pass 1: {len(p1)} departments (page 1)...")
    r1 = obscura_scrape(list(p1.keys()), EVAL_LIST)
    per_dept = {}        # slug -> {count, cards[]}
    for url, slug in p1.items():
        ev = r1.get(url)
        if not ev:
            per_dept[slug] = {"count": 0, "cards": []}
            continue
        obj = json.loads(ev)
        per_dept[slug] = {"count": obj.get("count", 0), "cards": obj.get("cards", [])}
        print(f"  {slug:32s} count={obj.get('count',0):3d} page1_cards={len(obj.get('cards',[]))}")

    # Pass 2 : extra pages for departments with count > PER_PAGE.
    extra = {}
    for slug, d in per_dept.items():
        pages = max(1, -(-d["count"] // PER_PAGE))  # ceil
        for pg in range(2, min(pages, 6) + 1):
            extra[url_for(slug, pg)] = slug
    if extra:
        print(f"Pass 2: {len(extra)} extra pages...")
        r2 = obscura_scrape(list(extra.keys()), EVAL_LIST)
        for url, slug in extra.items():
            ev = r2.get(url)
            if not ev:
                continue
            obj = json.loads(ev)
            per_dept[slug]["cards"].extend(obj.get("cards", []))

    # Merge + dedup by fiche link (fallback name+addr).
    seen, master = set(), []
    for slug, d in per_dept.items():
        code, region = DEPTS[slug]
        for c in d["cards"]:
            key = c.get("link") or (c["name"] + "|" + c["addr"])
            if key in seen:
                continue
            seen.add(key)
            master.append({
                "name": c["name"],
                "addr": c["addr"],
                "link": c.get("link", ""),
                "dept": code,
                "region": region,
            })
    (RAW / "master_list.json").write_text(
        json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTOTAL unique residences: {len(master)}")
    by_region = {}
    for m in master:
        by_region[m["region"]] = by_region.get(m["region"], 0) + 1
    print(f"By region: {by_region}")
    print(f"-> {RAW/'master_list.json'}")


def stage_geocode():
    print("== STAGE geocode (BAN api-adresse.data.gouv.fr) ==")
    import csv
    master = json.load(open(RAW / "master_list.json", encoding="utf-8"))
    for r in master:
        r["operator"] = detect_operator(r["name"])
    # Write CSV for BAN batch geocoder.
    csv_path = RAW / "addresses.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "adresse"])
        for i, r in enumerate(master):
            w.writerow([i, r["addr"]])
    out_csv = RAW / "geocoded.csv"
    print(f"POST {len(master)} addresses to BAN batch...")
    cmd = ["curl", "-s", "-X", "POST",
           "-F", f"data=@{csv_path}", "-F", "columns=adresse",
           "https://api-adresse.data.gouv.fr/search/csv/", "-o", str(out_csv)]
    subprocess.run(cmd, check=True)
    # Parse results, merge by idx.
    ok = 0
    with open(out_csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_idx = {int(row["idx"]): row for row in rows if row.get("idx", "").isdigit()}
    for i, r in enumerate(master):
        row = by_idx.get(i, {})
        lat, lng = row.get("latitude", ""), row.get("longitude", "")
        score = row.get("result_score", "") or "0"
        try:
            score = float(score)
        except ValueError:
            score = 0.0
        if lat and lng and score >= 0.35:
            r["lat"], r["lng"] = float(lat), float(lng)
            r["geo_score"] = round(score, 2)
            r["postal_code"] = row.get("result_postcode", "")
            r["city"] = row.get("result_city", "")
            citycode = row.get("result_citycode", "")
            if citycode[:2].isdigit():
                r["dept"] = citycode[:2] if citycode[:2] != "20" else r["dept"]
            ok += 1
        else:
            r["lat"], r["lng"], r["geo_score"] = None, None, round(score, 2)
            r["postal_code"], r["city"] = "", ""
    json.dump(master, open(RAW / "geocoded.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"Geocoded OK: {ok}/{len(master)}  (failed/low: {len(master)-ok})")
    ops = {}
    for r in master:
        ops[r["operator"]] = ops.get(r["operator"], 0) + 1
    print("Operators:", dict(sorted(ops.items(), key=lambda x: -x[1])))
    print(f"-> {RAW/'geocoded.json'}")


def stage_detail(limit=None):
    print("== STAGE detail (fiche pages -> contact/price/photo) ==")
    base = json.load(open(RAW / "geocoded.json", encoding="utf-8"))
    rows = [r for r in base if r.get("link")]
    if limit:
        rows = rows[:limit]
    urls = [r["link"] for r in rows]
    print(f"Scraping {len(urls)} fiche pages (concurrency 12)...")
    t0 = time.time()
    res = obscura_scrape(urls, EVAL_DETAIL, concurrency=12, timeout=45)
    failed = [u for u in urls if not res.get(u)]
    if failed:
        print(f"  retrying {len(failed)} failed pages...")
        res2 = obscura_scrape(failed, EVAL_DETAIL, concurrency=6, timeout=55)
        res.update({k: v for k, v in res2.items() if v})
    print(f"  scrape done in {int(time.time()-t0)}s")

    today = datetime.date.today().isoformat()
    final, enriched = [], 0
    for i, r in enumerate(rows):
        d = {}
        ev = res.get(r["link"])
        if ev:
            try:
                d = json.loads(ev)
            except json.JSONDecodeError:
                d = {}
        prices = d.get("prices", {}) or {}
        price_vals = [v for v in prices.values() if isinstance(v, int)]
        price_from = min(price_vals) if price_vals else None
        if d.get("phone") or d.get("website") or price_from:
            enriched += 1
        final.append({
            "id": i + 1,
            "name": r["name"],
            "operator": r.get("operator", "Indépendant / autre"),
            "dept": r["dept"],
            "region": r["region"],
            "address": r["addr"],
            "postal_code": r.get("postal_code", ""),
            "city": r.get("city", ""),
            "lat": r.get("lat"),
            "lng": r.get("lng"),
            "phone": d.get("phone", ""),
            "email": d.get("email", ""),
            "website": d.get("website", ""),
            "source_url": r["link"],
            "photo": d.get("photo", ""),
            "desc": d.get("desc", ""),
            "price_from": price_from,
            "price_unit": "€/mois" if d.get("monthly") else ("€" if price_from else ""),
            "prices": prices,
            "surface_min": d.get("surface_min"),
            "surface_max": d.get("surface_max"),
            "crawl_date": today,
        })
    out = ROOT / "data" / "residences.json"
    json.dump(final, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    with_phone = sum(1 for r in final if r["phone"])
    with_web = sum(1 for r in final if r["website"])
    with_price = sum(1 for r in final if r["price_from"])
    with_photo = sum(1 for r in final if r["photo"])
    print(f"\nFINAL: {len(final)} residences -> {out}")
    print(f"  phone:{with_phone}  website:{with_web}  price:{with_price}  photo:{with_photo}  enriched:{enriched}")


def stage_enrich():
    print("== STAGE enrich (official sites -> real photo / price / surface) ==")
    out_path = ROOT / "data" / "residences.json"
    data = json.load(open(out_path, encoding="utf-8"))
    # Drop dead sanitaire-social photo URLs (onpc.fr CDN returns 404).
    for r in data:
        if r.get("photo") and "onpc.fr" in r["photo"]:
            r["photo"] = ""
    targets = [r for r in data if r.get("website")]
    urls = [r["website"] for r in targets]
    print(f"Enriching {len(urls)} official sites (concurrency 10)...")
    t0 = time.time()
    res = obscura_scrape(urls, EVAL_ENRICH, concurrency=10, timeout=45)
    failed = [u for u in urls if not res.get(u)]
    if failed:
        print(f"  retrying {len(failed)} failed...")
        res.update({k: v for k, v in obscura_scrape(failed, EVAL_ENRICH, 6, 55).items() if v})
    print(f"  done in {int(time.time()-t0)}s")

    up_photo = up_price = up_surf = 0
    for r in targets:
        ev = res.get(r["website"])
        if not ev:
            continue
        try:
            d = json.loads(ev)
        except json.JSONDecodeError:
            continue
        if d.get("photo") and not r.get("photo"):
            r["photo"] = d["photo"]; up_photo += 1
        if d.get("price") and not r.get("price_from"):
            r["price_from"] = d["price"]
            r["price_unit"] = "€/mois" if d.get("monthly") else "€"
            up_price += 1
        if d.get("surface_min") and not r.get("surface_min"):
            r["surface_min"] = d["surface_min"]; r["surface_max"] = d["surface_max"]; up_surf += 1
    json.dump(data, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    tot = len(data)
    print(f"\nEnriched  +photo:{up_photo}  +price:{up_price}  +surface:{up_surf}")
    print(f"Coverage  photo:{sum(1 for r in data if r['photo'])}/{tot}  "
          f"price:{sum(1 for r in data if r['price_from'])}/{tot}  "
          f"phone:{sum(1 for r in data if r['phone'])}/{tot}")


def stage_deep(limit=None):
    print("== STAGE deep (official sites -> gallery / offers / services / description) ==")
    out_path = ROOT / "data" / "residences.json"
    data = json.load(open(out_path, encoding="utf-8"))
    targets = [r for r in data if r.get("website")]
    if limit:
        targets = targets[:limit]
    urls = [r["website"] for r in targets]
    print(f"Deep-crawling {len(urls)} official sites (concurrency 8)...")
    t0 = time.time()
    res = obscura_scrape(urls, EVAL_DEEP, concurrency=8, timeout=50)
    failed = [u for u in urls if not res.get(u)]
    if failed:
        print(f"  retrying {len(failed)} failed...")
        res.update({k: v for k, v in obscura_scrape(failed, EVAL_DEEP, 5, 55).items() if v})
    print(f"  done in {int(time.time()-t0)}s")

    up_gal = up_off = up_serv = up_desc = up_photo = 0
    for r in targets:
        ev = res.get(r["website"])
        if not ev:
            r.setdefault("gallery", []); r.setdefault("offers", [])
            r.setdefault("services", []); r.setdefault("description_long", "")
            continue
        try:
            d = json.loads(ev)
        except json.JSONDecodeError:
            d = {}
        gallery = [g for g in (d.get("gallery") or []) if g][:12]
        r["gallery"] = gallery
        r["offers"] = d.get("offers") or []
        r["services"] = d.get("services") or []
        r["description_long"] = (d.get("description") or "").strip()
        if gallery:
            up_gal += 1
        if r["offers"]:
            up_off += 1
        if r["services"]:
            up_serv += 1
        if r["description_long"]:
            up_desc += 1
        # promote first gallery image to the card photo if missing
        if gallery and not r.get("photo"):
            r["photo"] = gallery[0]; up_photo += 1
    # ensure all rows have the new keys (even those without a website)
    for r in data:
        r.setdefault("gallery", []); r.setdefault("offers", [])
        r.setdefault("services", []); r.setdefault("description_long", "")
    json.dump(data, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    tot = len(data)
    print(f"\nDeep results  +gallery:{up_gal}  +offers:{up_off}  +services:{up_serv}  +desc:{up_desc}  +photo:{up_photo}")
    print(f"Coverage  gallery:{sum(1 for r in data if r.get('gallery'))}/{tot}  "
          f"services:{sum(1 for r in data if r.get('services'))}/{tot}  "
          f"photo:{sum(1 for r in data if r.get('photo'))}/{tot}  "
          f"offers:{sum(1 for r in data if r.get('offers'))}/{tot}")
    galn = sum(len(r.get('gallery', [])) for r in data)
    print(f"Total gallery images: {galn}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "list"
    if stage == "list":
        stage_list()
    elif stage == "geocode":
        stage_geocode()
    elif stage == "detail":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
        stage_detail(lim)
    elif stage == "enrich":
        stage_enrich()
    elif stage == "deep":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
        stage_deep(lim)
    else:
        print(f"Unknown stage: {stage}")
