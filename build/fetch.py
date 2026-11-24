#!/usr/bin/env python3
"""Refreshes build/data/ from the Grand Encampment's public website, usagekt.org.

Everything here is read from public pages and the site's public WordPress
REST API; nothing is copied off usagekt.org except the page text. PDFs,
images and magazine issues stay where they are and are linked.

    python3 build/fetch.py      # then python3 build/build.py

data/pages.json      page HTML (cleaned later by build.py), keyed by slug
data/events.json     calendar events (Modern Events Calendar), with dates
data/statenews.json  monthly state supplements, current year and archive
data/articles.json   Knight Templar magazine article library (PDFs)
data/home.json       current notices and magazine issue from the home page
"""
from pathlib import Path
from html import unescape
from urllib.request import Request, urlopen
from urllib.parse import unquote, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
import json
import re
import sys

SRC = "https://usagekt.org"
DATA = Path(__file__).resolve().parent / "data"
UA = {"User-Agent": "Mozilla/5.0 (compatible; knightstemplar.dev demo builder)"}


def get(url, tries=3):
    for i in range(tries):
        try:
            with urlopen(Request(url, headers=UA), timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as ex:  # noqa: BLE001
            err = ex
    raise RuntimeError(f"{url}: {err}")


def text(h):
    h = re.sub(r"(?s)<(script|style|svg)[^>]*>.*?</\1>", " ", h or "")
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def links(h):
    """[(label, href)] for every <a> in a chunk of HTML."""
    out = []
    for m in re.finditer(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', h, re.S):
        label = text(m.group(2))
        if label:
            out.append((label, unescape(m.group(1))))
    return out


def save(name, data):
    (DATA / name).write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"  {name}", file=sys.stderr)


# ------------------------------------------------------------------ pages

def pages():
    raw = json.loads(get(f"{SRC}/wp-json/wp/v2/pages?per_page=100&_fields=id,slug,title,content,modified"))
    return {p["slug"]: {"title": text(p["title"]["rendered"]), "modified": p["modified"][:10],
                        "html": p["content"]["rendered"]} for p in raw}


# ------------------------------------------------------------------ events

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def event(ev):
    h = get(ev["link"])
    out = {"title": text(ev["title"]["rendered"]), "url": ev["link"], "slug": ev["slug"]}
    g = re.search(r'href="(https://calendar\.google\.com/calendar/render\?[^"]+)"', h)
    if g:
        q = parse_qs(urlparse(unescape(g.group(1))).query)
        d = (q.get("dates") or [""])[0].split("/")
        out["start"], out["end"] = d[0], (d[1] if len(d) > 1 else d[0])
    t = re.search(r'mec-single-event-time.*?<dd[^>]*>(.*?)</dd>', h, re.S)
    if t:
        out["time"] = text(t.group(1))
    place = re.search(r'class="author fn org">(.*?)</', h, re.S)
    addr = re.search(r'class="mec-address">(.*?)</', h, re.S)
    out["place"] = text(place.group(1)) if place else ""
    out["address"] = text(addr.group(1)) if addr else ""
    cat = re.search(r'mec-single-event-category.*?<dd[^>]*>(.*?)</dd>', h, re.S)
    out["category"] = text(cat.group(1)) if cat else ""
    body = re.search(r'mec-single-event-description mec-events-content">(.*?)<div class="mec-event-social', h, re.S)
    body = body.group(1) if body else ""
    out["files"] = [(l, u) for l, u in links(body) if u.lower().endswith(".pdf")]
    pdfs = re.findall(r'href="(https://usagekt\.org/wp-content/uploads/[^"]+\.pdf)"', body)
    if pdfs and not out["files"]:
        out["files"] = [("Event information (PDF)", pdfs[0])]
    img = re.search(r'<meta property="og:image" content="([^"]+)"', h)
    out["image"] = img.group(1) if img else ""
    return out


def events():
    raw = json.loads(get(f"{SRC}/wp-json/wp/v2/mec-events?per_page=100&_fields=slug,link,title"))
    with ThreadPoolExecutor(6) as pool:
        evs = [e for e in pool.map(event, raw) if e.get("start")]
    evs.sort(key=lambda e: e["start"])
    return evs


# ------------------------------------------------------------------ state news

def accordion(h):
    """Elementor accordion -> [(state, [(month, pdf)])]."""
    out = []
    for m in re.finditer(r"<details.*?</details>", h, re.S):
        block = m.group(0)
        title = re.search(r'e-n-accordion-item-title-text">(.*?)</div>', block, re.S)
        items = [(l, u) for l, u in links(block) if u.lower().endswith(".pdf")]
        if title and items:
            out.append([text(title.group(1)), items])
    return out


def statenews(pg):
    years = {}
    cur = accordion(pg["statenews"]["html"])
    m = re.search(r"/uploads/(\d{4})/", json.dumps(cur))
    years[m.group(1) if m else "current"] = cur
    for slug in sorted(pg):
        y = re.fullmatch(r"news(\d{4})", slug)
        if y:
            years[y.group(1)] = accordion(pg[slug]["html"])
    return {"years": dict(sorted(years.items(), reverse=True))}


# ------------------------------------------------------------------ articles

def articles(pg):
    feat = [(l, u) for l, u in links(pg["articles"]["html"]) if u.lower().endswith(".pdf")]
    by_year = {}
    for slug in sorted(pg):
        y = re.fullmatch(r"articles(\d{4})", slug)
        if y:
            by_year[y.group(1)] = [(l, u) for l, u in links(pg[slug]["html"]) if u.lower().endswith(".pdf")]
    famous = [(l, u) for l, u in links(pg.get("famous", {}).get("html", "")) if u.lower().endswith(".pdf")]
    return {"featured": feat, "years": by_year, "famous": famous}


# ------------------------------------------------------------------ home

def home():
    h = get(SRC + "/")
    body = h[h.find("Christmas"):] if "Christmas" in h else h
    notices = []
    for l, u in links(h):
        if "/wp-content/uploads/" in u and u.lower().endswith(".pdf") and "/2024/06/" not in u \
                and not any(u == x[1] for x in notices):
            notices.append((l, u))
    issue = re.search(r'href="(https://issuu\.com/knightstemplar/docs/[^"]+)"', h)
    cover = None
    if issue:
        i = h.find(issue.group(1))
        img = re.search(r'<img[^>]+src="([^"]+)"', h[i:i + 2000])
        cover = img.group(1) if img else None
    social = sorted({u for l, u in links(h) if re.search(r"facebook|x\.com|instagram|youtube", u)})
    return {"notices": notices, "issue": issue.group(1) if issue else "https://issuu.com/knightstemplar",
            "issue_cover": cover, "social": social}


def main():
    DATA.mkdir(exist_ok=True)
    print("Fetching usagekt.org ...", file=sys.stderr)
    pg = pages()
    save("pages.json", pg)
    save("statenews.json", statenews(pg))
    save("articles.json", articles(pg))
    save("home.json", home())
    save("events.json", events())


if __name__ == "__main__":
    main()
