#!/usr/bin/env python3
"""Builds every page in public/ for the knightstemplar.dev demonstration site.

A proposed redesign of usagekt.org, the website of the Grand Encampment of
Knights Templar of the U.S.A. Page text, the calendar, State News, magazine
articles and notices come from usagekt.org (refresh with
`python3 build/fetch.py`); PDFs, photos and magazine issues are linked where
they live. Edit this file, then run:

    python3 build/build.py

The generated HTML in public/ is committed; Cloudflare only serves it.
"""
from pathlib import Path
from html import escape, unescape
from html.parser import HTMLParser
from datetime import datetime, date, timedelta, timezone
import json
import re
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "public"
DATA = HERE / "data"
PAGES = json.loads((DATA / "pages.json").read_text())
EVENTS = json.loads((DATA / "events.json").read_text())
NEWS = json.loads((DATA / "statenews.json").read_text())
ARTICLES = json.loads((DATA / "articles.json").read_text())
HOME = json.loads((DATA / "home.json").read_text())

SITE = "https://knightstemplar.dev"
SRC = "https://usagekt.org"
NAME = "Grand Encampment of Knights Templar"
FULL = "Grand Encampment of Knights Templar of the United States of America"
TODAY = date.today()
UPDATED = TODAY.strftime("%B %-d, %Y")

ADDRESS = ["3 Sugar Creek Center Blvd., Suite 410", "Sugar Land, TX 77478"]
PHONE = "713-349-8700"
FAX = "713-349-8710"
EMAIL = "gr@usagekt.org"
EDUCATION = "https://templared.org"
ISSUU = "https://issuu.com/knightstemplar"
APPLE = "https://itunes.apple.com/us/app/knight-templar-magazine/id1422046085"
ANDROID = "https://play.google.com/store/apps/details?id=com.axiosdigital.KnightTemplar"
TRIENNIAL = "https://kt-triennial.org"
CS = [("Constitution, Statutes & Ceremonies, 2022", f"{SRC}/wp-content/uploads/2024/06/2022-GEKT-CS.pdf"),
      ("Constitution, Statutes & Ceremonies, 2019", f"{SRC}/wp-content/uploads/2024/06/2019-GEKT-CS.pdf")]

NAV = [
    ("/about/", "About"),
    ("/history/", "History"),
    ("/leadership/", "Leadership"),
    ("/calendar/", "Calendar"),
    ("/news/", "State News"),
    ("/magazine/", "Magazine"),
    ("/charities/", "Charities"),
    ("/resources/", "Resources"),
]

# ------------------------------------------------------------------ page map
# usagekt.org slug -> (path here, title, one-line summary). Sections group them.

SECTIONS = {
    "/about/": ("About the Order", "Who Knights Templar are, what the Grand Encampment does and how to join.", [
        ("about", "/about/who-we-are/", "Who we are", "The Order of Knights Templar today, and how it fits in Freemasonry."),
        ("mission", "/about/mission/", "Mission and vision", "To provide every Christian Freemason the opportunity to extend his Masonic journey through the chivalric experience."),
        ("howtojoin", "/about/join/", "How to join", "Who may petition a Commandery, and who to contact."),
        ("orders", "/about/orders/", "The chivalric orders", "The Order of the Red Cross, the Order of Malta and the Order of the Temple."),
        ("appendant", "/about/appendant-bodies/", "Appendant bodies", "Related orders and Templar bodies around the world."),
    ]),
    "/history/": ("History", "From the medieval Poor Fellow-Soldiers of Christ to the Grand Encampment, founded in 1816.", [
        ("origin", "/history/origin/", "Origin of the Knights Templar", "The medieval Order and the legends that grew around it."),
        ("heritage", "/history/heritage/", "Our Templar heritage", "Templary in the United States, from Masonic Americana."),
        ("founders", "/history/founders/", "The founders", "The Sir Knights who organized the Grand Encampment."),
        ("formation", "/history/formation/", "Formation of the Grand Encampment", "How the Grand Commanderies came together."),
        ("conclaves", "/history/triennial-conclaves/", "Triennial Conclaves", "Every Triennial Conclave since 1816."),
        ("honors", "/history/awards-and-honors/", "Awards and honors", "The Grand Encampment's honors and how they are earned."),
    ]),
    "/leadership/": ("Leadership", "The Grand Master, Grand Officers and Department Commanders serving this Triennium.", [
        ("go", "/leadership/grand-officers/", "Grand Officers", "The elected and appointed officers of the Grand Encampment."),
        ("redc", "/leadership/department-commanders/", "Department Commanders", "The Grand Master's representatives in each Department."),
        ("visits", "/leadership/visits/", "Grand Master's visits", "Official visits to Grand Commanderies."),
        ("bulletins", "/leadership/bulletins/", "Grand Master's bulletins", "Bulletins and messages from the Grand Master."),
        ("aides", "/leadership/aides/", "Aides", "Aides to the Grand Master, Grand Officers and Past Grand Masters."),
        ("committees", "/leadership/committees/", "Committees", "Standing and special committees."),
        ("coh", "/leadership/college-of-honors/", "College of Honors", "Jurisdictional deputies and members."),
        ("lpgm", "/leadership/living-past-grand-masters/", "Living Past Grand Masters", "Past Grand Masters who still serve the Order."),
        ("pgoarchive", "/leadership/past-grand-officers/", "Past Grand Officers", "Every Grand Officer since 1816, by office."),
        ("repdc", "/leadership/past-department-commanders/", "Past Department Commanders", "The full archive."),
    ]),
    "/charities/": ("Charities", "Knights Templar serve mankind through three great charities and the 40 Mile Project.", [
        ("charities", "/charities/overview/", "Our philanthropy", "The Eye Foundation, the Educational Foundation and the Holy Land Pilgrimage."),
        ("kteduf", "/charities/educational-foundation/", "Educational Foundation", "Grants and scholarships for higher education since 1922."),
        ("40miles", "/charities/40-mile-project/", "The 40 Mile Project", "Ask the Grand Prelate for prayer for yourself or someone you love."),
    ]),
    "/resources/": ("Resources", "Governing documents, uniforms, drill, education and the Grand Commanderies.", [
        ("gcsites", "/resources/grand-commanderies/", "Grand Commandery websites", "Find your state's Grand Commandery."),
        ("conferences", "/calendar/department-conferences/", "Department Conferences", "Every Department's next conference."),
        ("regalia", "/resources/uniforms-and-regalia/", "Uniforms and regalia", "Uniform rules and regalia suppliers."),
        ("drill", "/resources/drill-team/", "Drill team", "The Triennial drill competition."),
        ("newscriteria", "/news/criteria/", "State News criteria", "How to prepare and submit your state's supplement."),
    ]),
}

# Pages reached from other pages but not listed in a section.
EXTRA = {
    "pgm": ("/leadership/past-grand-officers/grand-masters/", "Past Grand Masters"),
    "pdgm": ("/leadership/past-grand-officers/deputy-grand-masters/", "Past Deputy Grand Masters"),
    "pgg": ("/leadership/past-grand-officers/grand-generalissimos/", "Past Grand Generalissimos"),
    "pgcg": ("/leadership/past-grand-officers/grand-captains-general/", "Past Grand Captains General"),
    "pgp": ("/leadership/past-grand-officers/grand-prelates/", "Past Grand Prelates"),
    "pgsw": ("/leadership/past-grand-officers/grand-senior-wardens/", "Past Grand Senior Wardens"),
    "pgjw": ("/leadership/past-grand-officers/grand-junior-wardens/", "Past Grand Junior Wardens"),
    "pgt": ("/leadership/past-grand-officers/grand-treasurers/", "Past Grand Treasurers"),
    "pgr": ("/leadership/past-grand-officers/grand-recorders/", "Past Grand Recorders"),
    "pgstb": ("/leadership/past-grand-officers/grand-standard-bearers/", "Past Grand Standard Bearers"),
    "pgswb": ("/leadership/past-grand-officers/grand-sword-bearers/", "Past Grand Sword Bearers"),
    "pgw": ("/leadership/past-grand-officers/grand-warders/", "Past Grand Warders"),
    "pgscog": ("/leadership/past-grand-officers/grand-sentinels/", "Past Grand Sentinels and Captains of the Guard"),
    "pgmar": ("/leadership/past-grand-officers/grand-marshals/", "Past Grand Marshals"),
    "dclinton": ("/history/grand-masters/dewitt-clinton/", "DeWitt Clinton"),
    "jnye": ("/history/grand-masters/jonathan-nye/", "Jonathan Nye"),
    "jmallen": ("/history/grand-masters/james-madison-allen/", "James Madison Allen"),
    "abull": ("/history/grand-masters/archibald-bull/", "Archibald Bull"),
    "wbhubbard": ("/history/grand-masters/william-blackstone-hubbard/", "William Blackstone Hubbard"),
    "bbfrench": ("/history/grand-masters/benjamin-b-french/", "Benjamin B. French"),
    "hlpalmer": ("/history/grand-masters/henry-lynde-palmer/", "Henry Lynde Palmer"),
    "wsgardner": ("/history/grand-masters/william-sewall-gardner/", "William Sewall Gardner"),
    "jqafellows": ("/history/grand-masters/john-quincy-adams-fellows/", "John Quincy Adams Fellows"),
    "jhhopkins": ("/history/grand-masters/james-h-hopkins/", "James H. Hopkins"),
    "hfowle": ("/history/founders/henry-fowle/", "Henry Fowle"),
    "jcsmith": ("/history/founders/john-corson-smith/", "John Corson Smith"),
    "jkstapleton": ("/history/founders/joseph-kendall-stapleton/", "Joseph Kendall Stapleton"),
    "jsnow": ("/history/founders/john-snow/", "John Snow"),
    "tlowndes": ("/history/founders/thomas-lowndes/", "Thomas Lowndes"),
    "tswebb": ("/history/founders/thomas-smith-webb/", "Thomas Smith Webb"),
}
EARLY_GMS = ["dclinton", "jnye", "jmallen", "abull", "wbhubbard", "bbfrench", "hlpalmer", "wsgardner",
             "jqafellows", "jhhopkins"]
FOUNDERS = ["tswebb", "hfowle", "jsnow", "jkstapleton", "tlowndes", "jcsmith"]

# Every usagekt.org path we know how to answer here.
LOCAL = {"": "/", "calendar": "/calendar/", "statenews": "/news/", "newsarchive": "/news/archive/",
         "articles": "/magazine/articles/", "famous": "/magazine/famous-masons/", "contact": "/contact/",
         "sitemap": "/", "2024drill": "/resources/drill-team/", "resources": "/resources/",
         "commanderies": "/resources/grand-commanderies/", "pgoarchive": "/leadership/past-grand-officers/"}
TITLES = {}
for sec, (_, _, items) in SECTIONS.items():
    for slug, path, title, _ in items:
        LOCAL[slug] = path
        TITLES[slug] = title
for slug, (path, title) in EXTRA.items():
    LOCAL[slug] = path
    TITLES[slug] = title
for y in NEWS["years"]:
    LOCAL[f"news{y}"] = f"/news/archive/{y}/"
for y in ARTICLES["years"]:
    LOCAL[f"articles{y}"] = f"/magazine/articles/#y{y}"


def e(t):
    return escape(str(t), quote=True)


def local_href(href):
    """Rewrite a usagekt.org page link to its page here; leave files and other sites alone."""
    h = unescape(href).strip()
    if h.startswith("//"):
        h = "https:" + h
    m = re.match(r"https?://(?:www\.)?usagekt\.org/([^?#]*)(#.*)?$", h)
    if m and "wp-content" not in m.group(1) and "KTMagazine" not in m.group(1):
        slug = m.group(1).strip("/")
        if slug in LOCAL:
            return LOCAL[slug]
    return h


# ------------------------------------------------------------------ html cleaner

ALLOWED = {"p", "h2", "h3", "h4", "ul", "ol", "li", "a", "strong", "em", "br", "table", "thead", "tbody",
           "tr", "th", "td", "blockquote", "img", "figure", "figcaption", "hr", "sup", "sub", "details", "summary"}
RENAME = {"b": "strong", "i": "em", "h1": "h2", "h5": "h4", "h6": "h4"}
DROP = {"script", "style", "svg", "form", "noscript", "button", "select", "textarea", "iframe", "input",
        "label", "video", "audio", "canvas", "template", "nav"}
VOID = {"br", "img", "hr"}


class Cleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.stack = [], 0, []

    def handle_starttag(self, tag, attrs):
        if tag in DROP:
            if tag not in VOID:
                self.skip += 1
            return
        if self.skip:
            return
        tag = RENAME.get(tag, tag)
        if tag not in ALLOWED:
            if tag in ("div", "section", "article") and self.out and not self.out[-1].endswith("\n"):
                self.out.append("\n")
            return
        a = dict(attrs)
        extra = ""
        if tag == "a":
            href = local_href(a.get("href") or "")
            # /_pda/ files are members-only on usagekt.org and answer 404 to the public.
            if not href or href.startswith(("#elementor", "javascript")) or href == "#" or "/_pda/" in href:
                self.stack.append(None)
                return
            extra = f' href="{e(href)}"'
            if href.startswith("http") and "usagekt.org/wp-content" not in href and not href.startswith(SITE):
                extra += ' rel="noopener"'
            if "elementor-button" in (a.get("class") or ""):
                extra += ' class="btn btn-quiet"'
        elif tag == "img":
            src = (a.get("src") or "").strip()
            if src.startswith("//"):
                src = "https:" + src
            if not src.startswith("https://") or "data:image" in src:
                return
            alt = a.get("alt") or ""
            dims = "".join(f' {k}="{e(a[k])}"' for k in ("width", "height") if (a.get(k) or "").isdigit())
            self.out.append(f'<img src="{e(src)}" alt="{e(alt)}"{dims} loading="lazy" decoding="async">')
            return
        elif tag in ("td", "th"):
            for k in ("colspan", "rowspan"):
                if (a.get(k) or "").isdigit():
                    extra += f' {k}="{a[k]}"'
        if tag in VOID:
            self.out.append(f"<{tag}>")
            return
        self.stack.append(tag)
        self.out.append(f"<{tag}{extra}>")

    def handle_endtag(self, tag):
        if tag in DROP:
            if tag not in VOID:
                self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        tag = RENAME.get(tag, tag)
        if tag not in ALLOWED or tag in VOID:
            return
        # close up to the matching open tag
        if tag in [t for t in self.stack if t]:
            while self.stack:
                t = self.stack.pop()
                if t:
                    self.out.append(f"</{t}>")
                if t == tag:
                    break
        elif None in self.stack and tag == "a":
            self.stack.remove(None)

    def handle_data(self, data):
        if not self.skip:
            self.out.append(escape(data, quote=False))

    def result(self):
        while self.stack:
            t = self.stack.pop()
            if t:
                self.out.append(f"</{t}>")
        return "".join(self.out)


def clean(html, title=""):
    c = Cleaner()
    c.feed(html)
    h = c.result()
    h = re.sub(r"[ \t\r\f\v]+", " ", h)
    h = re.sub(r"\s*\n\s*", "\n", h)
    for _ in range(4):  # empty elements left by layout markup
        h = re.sub(r"<(p|h2|h3|h4|li|ul|ol|strong|em|a|blockquote|figure|summary)(?: [^>]*)?>(?:\s|&nbsp;|\xa0|<br>)*</\1>", "", h)
    # Loose text between blocks becomes paragraphs.
    parts = re.split(r"(<(?:/?(?:p|h2|h3|h4|ul|ol|li|table|thead|tbody|tr|th|td|blockquote|figure|figcaption|hr|details|summary)\b[^>]*)>)", h)
    out, depth = [], 0
    for p in parts:
        if p.startswith("<") and re.match(r"</?(p|h2|h3|h4|ul|ol|li|table|thead|tbody|tr|th|td|blockquote|figure|figcaption|hr|details|summary)\b", p):
            if re.match(r"<(p|h2|h3|h4|li|td|th|blockquote|figcaption|summary)\b", p):
                depth += 1
            elif re.match(r"</(p|h2|h3|h4|li|td|th|blockquote|figcaption|summary)\b", p):
                depth = max(0, depth - 1)
            out.append(p)
        elif depth == 0 and p.strip() and re.sub(r"<[^>]+>", "", p).strip():
            for chunk in re.split(r"(?:\s*<br>\s*){2,}", p.strip()):
                if chunk.strip():
                    out.append(f"<p>{chunk.strip()}</p>")
        else:
            out.append(p)
    h = "".join(out)
    # The page title is already the <h1>; drop the first heading if it repeats it.
    first = re.match(r"\s*<h[23][^>]*>(.*?)</h[23]>", h, re.S)
    if first and title and re.sub(r"\W+", "", unescape(re.sub(r"<[^>]+>", "", first.group(1))).lower()) in (
            re.sub(r"\W+", "", title.lower()), re.sub(r"\W+", "", PAGES_TITLE.get(title, "").lower())):
        h = h[first.end():]
    h = re.sub(r"<table>", '<div class="table"><table>', h)
    h = re.sub(r"</table>", "</table></div>", h)
    return h.strip()


PAGES_TITLE = {}


# ------------------------------------------------------------------ icons

ICON = {
    "cal": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "pin": '<path d="M12 22s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/>',
    "file": '<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    "out": '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "book": '<path d="M4 4h6a3 3 0 0 1 3 3v13a2 2 0 0 0-2-2H4z"/><path d="M20 4h-6a3 3 0 0 0-3 3v13a2 2 0 0 1 2-2h7z"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    "rss": '<path d="M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
}


def icon(name, size=18):
    return (f'<svg class="i" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[name]}</svg>')


THEME_BTN = ('<button class="theme-btn" type="button" aria-pressed="false" aria-label="Dark mode" '
             'title="Switch light or dark mode" hidden>'
             '<svg class="i i-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
             'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>'
             '<svg class="i i-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
             'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2'
             'M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button>')


# ------------------------------------------------------------------ layout

def page(path, title, body, desc="", wide=False, crumbs=None):
    full_title = f"{title} | {NAME}" if path != "/" else f"{NAME} of the U.S.A."
    desc = desc or f"{title}: from the {FULL}."
    nav = "".join(
        f'<li><a href="{href}"{" aria-current=page" if path == href or (href != "/" and path.startswith(href)) else ""}>{label}</a></li>'
        for href, label in NAV)
    bc = ""
    if crumbs:
        trail = "".join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in crumbs)
        bc = f'<nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li>{trail}</ol></nav>'
    social = "".join(
        f'<li><a href="{e(u)}" rel="noopener">{n}</a></li>' for n, u in
        [(re.sub(r"^www\.|\.com$", "", re.sub(r"https?://([^/]+).*", r"\1", u)).replace("x", "X", 1)
          .replace("facebook", "Facebook").replace("instagram", "Instagram").replace("youtube", "YouTube"), u)
         for u in HOME.get("social", [])])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{NAME}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}/img/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Seal of the Grand Encampment of Knights Templar of the U.S.A.">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="alternate" type="text/calendar" title="Grand Encampment calendar" href="/calendar.ics">
<script>try{{var t=localStorage.getItem("theme");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}}catch(e){{}}document.documentElement.classList.add("js")</script>
<link rel="preload" href="/fonts/frank-ruhl-libre-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/site.css">
<script src="/site.js" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
<div class="demo-bar" role="note"><div class="wrap"><strong>Demonstration site.</strong> A proposed redesign of <a href="{SRC}/" rel="noopener">usagekt.org</a>, built from its own public content. Not an official Grand Encampment website. <a href="/about-this-demo/">About this demo</a></div></div>
<header class="site-head">
<div class="wrap head-row">
<a class="brand" href="/"><img src="/img/gekt/wordmark.webp" alt="Grand Encampment of Knights Templar of the U.S.A., home" width="306" height="60"></a>
<div class="head-tools">
<a class="head-link" href="/contact/">Contact</a>
{THEME_BTN}
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="site-nav" hidden>{icon("menu", 20)}<span>Menu</span></button>
</div>
</div>
<nav id="site-nav" class="site-nav" aria-label="Main"><ul class="wrap">{nav}</ul></nav>
</header>
<main id="main"{' class="wide"' if wide else ''}>
{bc}
{body}
</main>
<footer class="site-foot">
<div class="wrap foot-grid">
<div>
<p class="foot-name">{FULL}</p>
<p>Grand Recorder's Office<br>{ADDRESS[0]}<br>{ADDRESS[1]}</p>
<p><a href="tel:+1{PHONE.replace('-', '')}">{PHONE}</a> · <a href="mailto:{EMAIL}">{EMAIL}</a></p>
</div>
<div>
<p class="foot-h">Explore</p>
<ul><li><a href="/about/join/">How to join</a></li><li><a href="/calendar/">Calendar</a></li><li><a href="/news/">State News</a></li><li><a href="/magazine/">Knight Templar magazine</a></li><li><a href="{EDUCATION}" rel="noopener">Education portal</a></li><li><a href="/charities/40-mile-project/">Prayer requests</a></li></ul>
</div>
<div>
<p class="foot-h">Follow</p>
<ul>{social}</ul>
</div>
</div>
<div class="wrap foot-note"><p>Demonstration redesign by <a href="https://creativetechnologypartners.com" rel="noopener">Creative Technology Partners</a>. Content, documents and photos belong to the Grand Encampment and are drawn from <a href="{SRC}/" rel="noopener">usagekt.org</a>; last refreshed {UPDATED}.</p></div>
</footer>
</body>
</html>
"""


# usagekt.org blocks its images from being shown on other sites (hotlink
# protection), so pages here don't embed them. Files and pages are still linked.
HOTLINK_IMG = re.compile(r'<img[^>]+src="https://usagekt\.org/[^"]*"[^>]*>')
# usagekt.org images we have our own copies of (from Mark's 2024 knightstemplar.dev backup),
# keyed by usagekt file name -> (local file, width, height). Everything else is stripped.
LOCAL_IMG = {
    "tswebb.jpg": ("webb", 171, 250), "hfowle.jpg": ("fowle", 176, 250), "jsnow.jpg": ("snow", 185, 250),
    "jkstapleton.jpg": ("stapleton", 160, 250), "tlowndes.jpg": ("lowndes", 144, 250), "jcsmith.jpg": ("smith", 152, 250),
    "kbfischer.png": ("fischer", 166, 250), "whkoon.png": ("koon", 164, 249), "ddgoodwin.png": ("goodwin", 164, 249),
    "dlvaught.png": ("vaught", 164, 249), "jnnelson.png": ("nelson", 180, 250), "kussman.png": ("kussman", 234, 350),
    "ktef.png": ("ktef", 240, 240), "edu.png": ("ktedu", 240, 240), "hlp.gif": ("kthlp", 240, 236), "40-miles.gif": ("40miles", 240, 240),
}
IMG_SRC = re.compile(r'<img[^>]+src="https://usagekt\.org/[^"]*/([^"/]+)"[^>]*>')


def local_img(m):
    hit = LOCAL_IMG.get(m.group(1))
    if not hit:
        return m.group(0)
    alt = re.search(r'alt="([^"]*)"', m.group(0))
    name, w, h = hit
    return f'<img class="portrait" src="/img/gekt/{name}.webp" alt="{alt.group(1) if alt else ""}" width="{w}" height="{h}" loading="lazy">'


IMG_LINK = re.compile(r'<a href="https://usagekt\.org/[^"]+\.(?:png|jpe?g|gif|webp)">\s*(<img class="portrait"[^>]*>)?\s*</a>')


PORTRAIT_ENTRY = re.compile(r'(<img class="portrait"[^>]*>)\s*(<p>\d{4}\s*-\s*\d{4}</p><p>.*?</p>)')


def write(path, html):
    html = IMG_LINK.sub(lambda m: m.group(1) or "", HOTLINK_IMG.sub("", IMG_SRC.sub(local_img, html)))
    html = PORTRAIT_ENTRY.sub(r'<div class="pgm">\1<div>\2</div></div>', html)
    out = ROOT / path.strip("/") / "index.html" if not path.endswith(".html") else ROOT / path.strip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def hero(title, lede="", kicker=""):
    k = f'<p class="kicker">{e(kicker)}</p>' if kicker else ""
    l = f'<p class="lede">{lede}</p>' if lede else ""
    return f'<div class="page-head"><div class="wrap">{k}<h1>{e(title)}</h1>{l}</div></div>'


def source_note(slug):
    p = PAGES.get(slug)
    if not p:
        return ""
    url = f"{SRC}/{slug}/" if slug else f"{SRC}/"
    return (f'<p class="src-note">From <a href="{url}" rel="noopener">usagekt.org/{slug}</a>'
            f', last updated there {datetime.strptime(p["modified"], "%Y-%m-%d").strftime("%B %-d, %Y")}.</p>')


def cards(items, cls="cards"):
    return f'<ul class="{cls}">' + "".join(
        f'<li><a href="{href}"><span class="c-title">{e(t)}</span>'
        + (f'<span class="c-sub">{e(s)}</span>' if s else "") + "</a></li>"
        for href, t, s in items) + "</ul>"


def file_link(label, url, cls=""):
    is_pdf = url.lower().endswith(".pdf")
    ic = icon("file") if is_pdf else icon("out")
    suffix = ' <span class="tag">PDF</span>' if is_pdf else ""
    return f'<a class="file {cls}" href="{e(url)}" rel="noopener">{ic}<span>{e(label)}{suffix}</span></a>'


# ------------------------------------------------------------------ events

def parse_dt(v):
    v = v.strip()
    if "T" in v:
        return datetime.strptime(v.rstrip("Z"), "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    return datetime.strptime(v, "%Y%m%d").replace(tzinfo=timezone.utc)


# Upcoming dates published elsewhere on usagekt.org (notices, the Department
# Conferences page) or by the Triennial committee, which the usagekt.org
# calendar does not list yet. Each one names its source.
CURATED = [
    {"title": "97th Annual Easter Observance", "day": "2027-03-28", "time": "Memorial service 8:00 am",
     "place": "George Washington Masonic National Memorial", "address": "101 Callahan Dr, Alexandria, VA 22301",
     "category": "Religious",
     "files": [["Announcement", f"{SRC}/wp-content/uploads/2026/10/2027_GEKT_Easter_Announcement.pdf"],
               ["Information", f"{SRC}/wp-content/uploads/2026/10/2027_GEKT_Easter_Information.pdf"],
               ["Credit card authorization", f"{SRC}/wp-content/uploads/2026/10/2027_GEKT_Easter_CC_Authorization.pdf"]]},
    {"title": "East Central Department Conference", "day": "2027-03-13", "place": "Grand Wayne Convention Center",
     "address": "Fort Wayne, IN", "category": "Department Conference", "files": [["Department Conferences", "/calendar/department-conferences/"]]},
    {"title": "Southeastern Department Conference", "day": "2027-06-10", "end": "2027-06-12",
     "address": "Kissimmee, FL", "category": "Department Conference", "files": [["Department Conferences", "/calendar/department-conferences/"]]},
    {"title": "70th Triennial Conclave", "day": "2027-08-12", "end": "2027-08-18",
     "place": "Los Angeles Marriott Burbank Airport", "address": "Burbank, CA", "category": "Triennial Conclave",
     "files": [["kt-triennial.org", TRIENNIAL]]},
    {"title": "Northeastern Department Conference", "day": "2026-09-11", "end": "2026-09-12", "address": "Albany, NY",
     "category": "Department Conference", "files": [["Department Conferences", "/calendar/department-conferences/"]]},
    {"title": "South Central Department Conference", "day": "2026-09-18", "address": "Little Rock, AR",
     "category": "Department Conference", "files": [["Department Conferences", "/calendar/department-conferences/"]]},
    {"title": "Mid-Atlantic Department Conference", "day": "2026-09-25", "end": "2026-09-26",
     "category": "Department Conference", "files": [["Department Conferences", "/calendar/department-conferences/"]]},
    {"title": "Northwestern Department Conference", "day": "2026-10-16",
     "category": "Department Conference", "files": [["Department Conferences", "/calendar/department-conferences/"]]},
    {"title": "North Central Department Conference", "day": "2026-10-23", "end": "2026-10-24", "address": "Sioux Falls, SD",
     "category": "Department Conference", "files": [["Department Conferences", "/calendar/department-conferences/"]]},
    {"title": "Southwestern Department Conference", "day": "2026-10-30",
     "category": "Department Conference", "files": [["Department Conferences", "/calendar/department-conferences/"]]},
]


def all_events():
    evs = []
    for ev in EVENTS:
        s, en = parse_dt(ev["start"]), parse_dt(ev["end"])
        all_day = (ev.get("time") or "").lower() == "all day"
        if all_day:
            # Stored as midnight Eastern in UTC; the date is what matters.
            s = (s - timedelta(hours=5)).date()
            en = (en - timedelta(hours=5) - timedelta(days=1)).date()
            en = max(en, s)
        else:
            s, en = s.astimezone(timezone(timedelta(hours=-5))).date(), en.astimezone(timezone(timedelta(hours=-5))).date()
        evs.append({**ev, "s": s, "e": en, "time": "" if all_day else ev.get("time", ""), "src": ev["url"]})
    have = {(x["title"].lower().replace("-", " "), x["s"]) for x in evs}
    for c in CURATED:
        s = date.fromisoformat(c["day"])
        if (c["title"].lower().replace("-", " "), s) in have:
            continue
        evs.append({**c, "s": s, "e": date.fromisoformat(c.get("end", c["day"])), "src": "",
                    "slug": re.sub(r"[^a-z0-9]+", "-", c["title"].lower()).strip("-") + f"-{s.year}"})
    evs.sort(key=lambda x: (x["s"], x["title"]))
    return evs


def when(ev):
    s, en = ev["s"], ev["e"]
    if en == s:
        return s.strftime("%A, %B %-d, %Y")
    if s.month == en.month:
        return f"{s.strftime('%B %-d')}–{en.day}, {s.year}"
    return f"{s.strftime('%B %-d')} – {en.strftime('%B %-d, %Y')}"


def event_card(ev, compact=False):
    where = ", ".join(x for x in [ev.get("place"), ev.get("address")] if x)
    files = ev.get("files") or []
    links = "".join(f"<li>{file_link(l, u)}</li>" for l, u in files)
    more = f'<a class="ev-src" href="{e(ev["src"])}" rel="noopener">Event page on usagekt.org</a>' if ev.get("src") and not compact else ""
    cat = f'<span class="ev-cat">{e(ev["category"])}</span>' if ev.get("category") else ""
    return (f'<article class="ev"><div class="ev-date" aria-hidden="true"><span class="m">{ev["s"].strftime("%b")}</span>'
            f'<span class="d">{ev["s"].day}</span></div><div class="ev-body">{cat}<h3>{e(ev["title"])}</h3>'
            f'<p class="ev-when">{icon("cal", 16)} {when(ev)}{(" · " + e(ev["time"])) if ev.get("time") else ""}</p>'
            + (f'<p class="ev-where">{icon("pin", 16)} {e(where)}</p>' if where else "")
            + (f'<ul class="ev-files">{links}</ul>' if links and not compact else "") + more + "</div></article>")


def ics(evs):
    def esc(t):
        return re.sub(r"([,;\\])", r"\\\1", t or "").replace("\n", "\\n")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//knightstemplar.dev//Grand Encampment calendar//EN",
             "CALSCALE:GREGORIAN", "X-WR-CALNAME:Grand Encampment of Knights Templar", "X-WR-TIMEZONE:America/Chicago"]
    for ev in evs:
        where = ", ".join(x for x in [ev.get("place"), ev.get("address")] if x)
        lines += ["BEGIN:VEVENT", f"UID:{ev['slug']}@knightstemplar.dev", f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{ev['s'].strftime('%Y%m%d')}",
                  f"DTEND;VALUE=DATE:{(ev['e'] + timedelta(days=1)).strftime('%Y%m%d')}",
                  f"SUMMARY:{esc(ev['title'])}"]
        if where:
            lines.append(f"LOCATION:{esc(where)}")
        desc = " ".join(x for x in [ev.get("time"), ev.get("category")] if x)
        if desc:
            lines.append(f"DESCRIPTION:{esc(desc)}")
        if ev.get("src"):
            lines.append(f"URL:{ev['src']}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    folded = []
    for ln in lines:
        while len(ln.encode()) > 74:
            cut = 74
            while len(ln[:cut].encode()) > 74:
                cut -= 1
            folded.append(ln[:cut])
            ln = " " + ln[cut:]
        folded.append(ln)
    return "\r\n".join(folded) + "\r\n"


# ------------------------------------------------------------------ state news

def latest_news(limit=8):
    """Most recent supplement per state from the current year, newest first."""
    year = next(iter(NEWS["years"]))
    order = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                         "September", "October", "November", "December"])}
    rows = []
    for state, items in NEWS["years"][year]:
        month, url = max(items, key=lambda x: order.get(x[0].strip(), -1))
        rows.append((order.get(month.strip(), -1), state.strip(), month.strip(), url))
    rows.sort(key=lambda r: (-r[0], r[1]))
    return year, rows[:limit]


def news_table(year, items, current=False):
    rows = "".join(
        f'<tr><th scope="row">{e(state.strip())}</th><td><ul class="chips">'
        + "".join(f'<li><a href="{e(u)}" rel="noopener">{e(m.strip()[:3])}<span class="vh"> {e(m.strip())} {year} (PDF)</span></a></li>' for m, u in months)
        + "</ul></td></tr>" for state, months in items)
    return (f'<div class="news-filter"><label for="nf">{icon("search", 16)} Find a state</label>'
            f'<input id="nf" type="search" autocomplete="off" placeholder="Type a state name" data-filter="#news-{year}"></div>'
            f'<div class="table"><table id="news-{year}" class="news"><caption class="vh">State News supplements, {year}</caption>'
            f'<thead><tr><th scope="col">Grand Commandery</th><th scope="col">Monthly supplements</th></tr></thead>'
            f"<tbody>{rows}</tbody></table></div>")


# ------------------------------------------------------------------ builders

def officers():
    """Grand Officers from usagekt.org/go/: photo, name, office, biography PDF, email."""
    h = PAGES.get("go", {}).get("html", "")
    parts = re.split(r'<a[^>]+href="((?:https:)?//usagekt\.org/wp-content/uploads/[^"]+\.(?:png|jpe?g|webp))"', h)
    out = []
    for i in range(1, len(parts) - 1, 2):
        photo, seg = parts[i], parts[i + 1].split(">", 1)[-1]
        photo = "https:" + photo if photo.startswith("//") else photo
        anchors = [(re.sub(r"<[^>]+>", "", b).strip(), a) for a, b in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', seg, re.S)]
        bio = next((a for l, a in anchors if l.startswith("Biography") and "/_pda/" not in a), "")
        mail = re.search(r'mailto:([^"]+)"', seg)
        lines = [x.strip() for x in unescape(re.sub(r"<[^>]+>", "\n", re.sub(r"(?s)<a[^>]*>.*?</a>", "", seg))).split("\n")]
        lines = [x for x in lines if x and x not in ("Biography", "Theme") and "@" not in x]
        if len(lines) < 2:
            continue
        name, office = lines[0], lines[1]
        if name.startswith("Associate"):
            name, office = office, name
        name = re.sub(r"^(S\.K\.|SK)\s+", "", name)
        out.append({"photo": photo, "name": name, "office": office, "bio": unescape(bio),
                    "email": mail.group(1) if mail else ""})
    return out


def officers_html():
    cards_ = []
    for o in officers():
        links = []
        if o["bio"]:
            links.append(f'<a href="{e(o["bio"])}" rel="noopener">Biography<span class="vh"> of {e(o["name"])}</span> <span class="tag">PDF</span></a>')
        if o["email"]:
            links.append(f'<a href="mailto:{e(o["email"])}">{e(o["email"])}</a>')
        cards_.append(f'<li class="officer"><img src="{e(o["photo"])}" alt="" width="200" height="300" loading="lazy">'
                      f'<p class="o-office">{e(o["office"])}</p><h2>Sir Knight {e(o["name"])}</h2>'
                      f'<p class="o-links">{"<br>".join(links)}</p></li>')
    return f'<ul class="officers">{"".join(cards_)}</ul>'


def build_content_pages():
    for sec, (stitle, _, items) in SECTIONS.items():
        for slug, path, title, summary in items:
            if slug not in PAGES:
                continue
            body = clean(PAGES[slug]["html"], title)
            if slug == "gcsites":
                body = f'<div class="cols-list">{body}</div>'
            if slug == "go" and officers():
                body = officers_html()
            extra = ""
            if slug == "founders":
                extra = "<h2>Founders' biographies</h2>" + cards([(LOCAL[s], EXTRA[s][1], "") for s in FOUNDERS], "cards small")
            if slug == "conclaves":
                extra = "<h2>The first ten Grand Masters</h2>" + cards([(LOCAL[s], EXTRA[s][1], "") for s in EARLY_GMS], "cards small")
            if slug == "40miles":
                body = re.sub(r"(?s)<p>[^<]*Contact Form[^<]*</p>", "", body)
                extra = (f'<p class="callout">The 40 Mile Project request form is on usagekt.org. '
                         f'<a class="btn" href="{SRC}/40miles/" rel="noopener">Submit a prayer request</a></p>')
            if slug == "regalia":
                extra = "<h2>Governing documents</h2><ul class=\"files\">" + "".join(f"<li>{file_link(l, u)}</li>" for l, u in CS) + "</ul>"
            if slug == "bulletins":
                body = body or "<p>The Grand Master's bulletins are posted as PDFs.</p>"
            html = (hero(title, e(summary), stitle) + f'<div class="wrap{"" if slug == "go" else " prose"}">{body}{extra}{source_note(slug)}</div>')
            write(path, page(path, title, html, summary, crumbs=[(sec, stitle)]))
    for slug, (path, title) in EXTRA.items():
        if slug not in PAGES:
            continue
        parent = "/leadership/past-grand-officers/" if path.startswith("/leadership") else (
            "/history/triennial-conclaves/" if "grand-masters" in path else "/history/founders/")
        ptitle = {"/leadership/past-grand-officers/": "Past Grand Officers",
                  "/history/triennial-conclaves/": "Triennial Conclaves", "/history/founders/": "The founders"}[parent]
        sec = "/" + path.split("/")[1] + "/"
        body = clean(PAGES[slug]["html"], title)
        html = hero(title, "", ptitle) + f'<div class="wrap prose">{body}{source_note(slug)}</div>'
        write(path, page(path, title, html, crumbs=[(sec, SECTIONS[sec][0]), (parent, ptitle)]))


def build_sections():
    for sec, (title, lede, items) in SECTIONS.items():
        extra = ""
        if sec == "/about/":
            extra = (f'<section class="band"><h2>The three orders of the Commandery</h2><ul class="orders">'
                     f'<li><img src="/img/red-cross.svg" alt="" width="72" height="72"><span>Illustrious Order of the Red Cross</span></li>'
                     f'<li><img src="/img/malta.svg" alt="" width="72" height="72"><span>Order of Malta</span></li>'
                     f'<li><img src="/img/temple.svg" alt="" width="72" height="72"><span>Order of the Temple</span></li></ul>'
                     f'<p><a class="btn" href="/about/orders/">About the orders</a></p></section>')
        if sec == "/resources/":
            extra = ('<h2>Documents and programs</h2><ul class="files">'
                     + "".join(f"<li>{file_link(l, u)}</li>" for l, u in CS + [
                         ("Commissioned Templar Chaplain program", f"{SRC}/wp-content/uploads/2024/08/ctp.pdf"),
                         ("York Rite 3 Minute Drill", f"{SRC}/wp-content/uploads/2024/08/yr3md.pdf"),
                         ("Templar Education Portal (templared.org)", EDUCATION),
                         ("York Rite Leadership Program", "https://yorkriteleadership.org/")])
                     + "</ul>")
        if sec == "/history/":
            extra = ("<h2>Early Grand Masters</h2>" + cards([(LOCAL[s], EXTRA[s][1], "") for s in EARLY_GMS], "cards small")
                     + "<h2>Founders</h2>" + cards([(LOCAL[s], EXTRA[s][1], "") for s in FOUNDERS], "cards small"))
        body = hero(title, e(lede)) + f'<div class="wrap">{cards([(p, t, s) for _, p, t, s in items])}{extra}</div>'
        write(sec, page(sec, title, body, lede))


def build_calendar(evs):
    today = TODAY
    up = [x for x in evs if x["e"] >= today]
    past = [x for x in evs if x["e"] < today and x["s"] >= today - timedelta(days=400)][::-1]

    def grouped(lst):
        out, cur = [], None
        for x in lst:
            k = x["s"].strftime("%B %Y")
            if k != cur:
                if cur:
                    out.append("</div>")
                out.append(f'<h2 class="month">{k}</h2><div class="ev-list">')
                cur = k
            out.append(event_card(x))
        if cur:
            out.append("</div>")
        return "".join(out)
    cats = sorted({x.get("category") for x in up if x.get("category")})
    filt = ('<div class="ev-filter" role="group" aria-label="Show"><button type="button" aria-pressed="true" data-cat="">All</button>'
            + "".join(f'<button type="button" aria-pressed="false" data-cat="{e(c)}">{e(c)}</button>' for c in cats) + "</div>") if cats else ""
    body = (hero("Calendar", "Easter Observance, Department Conferences, Grand Conclaves and the Triennial Conclave.", "Events")
            + f'<div class="wrap"><div class="cal-tools"><a class="btn" href="/calendar.ics">{icon("cal")} Subscribe to this calendar</a>'
            f'<a class="btn btn-quiet" href="/calendar/department-conferences/">Department Conferences</a></div>{filt}'
            + f'<div id="upcoming">{grouped(up) if up else "<p>No upcoming events are posted yet.</p>"}</div>'
            + (f'<details class="past"><summary>Past events ({len(past)})</summary>{grouped(past)}</details>' if past else "")
            + '<p class="src-note">Events come from the <a href="https://usagekt.org/calendar/" rel="noopener">usagekt.org calendar</a>, '
              'plus dates the Grand Encampment has announced in notices and on its Department Conferences page that the calendar does not show yet. '
              'Subscribe once and new events appear in Google, Apple or Outlook calendars on their own.</p></div>')
    write("/calendar/", page("/calendar/", "Calendar", body, "Upcoming Grand Encampment events: Easter Observance, Department Conferences, Grand Conclaves and the Triennial Conclave."))
    (ROOT / "calendar.ics").write_text(ics(evs))
    return up


def build_news():
    years = list(NEWS["years"])
    cur = years[0]
    arch = cards([(f"/news/archive/{y}/", f"State News {y}", f"{len(NEWS['years'][y])} Grand Commanderies") for y in years[1:]], "cards small")
    body = (hero(f"State News {cur}", "Each Grand Commandery's monthly supplement to the Knight Templar magazine, in one place.", "Knight Templar State News")
            + f'<div class="wrap">{news_table(cur, NEWS["years"][cur], True)}<h2>Archive</h2>{arch}'
            + f'<p><a href="/news/criteria/">How to prepare and submit your State News</a></p>'
            + f'<p class="src-note">Supplements are published on <a href="{SRC}/statenews/" rel="noopener">usagekt.org</a>; each link opens the PDF there.</p></div>')
    write("/news/", page("/news/", f"State News {cur}", body, "Monthly State News supplements from every Grand Commandery."))
    write("/news/archive/", page("/news/archive/", "State News archive", hero("State News archive", "Past years of State News supplements.", "Knight Templar State News") + f'<div class="wrap">{arch}</div>', crumbs=[("/news/", "State News")]))
    for y in years[1:]:
        body = hero(f"State News {y}", "", "State News archive") + f'<div class="wrap">{news_table(y, NEWS["years"][y])}</div>'
        write(f"/news/archive/{y}/", page(f"/news/archive/{y}/", f"State News {y}", body, crumbs=[("/news/", "State News"), ("/news/archive/", "Archive")]))


def build_magazine():
    cover = HOME.get("issue_cover")
    issue = HOME.get("issue") or ISSUU
    name = re.sub(r"[_-]+", " ", issue.rstrip("/").rsplit("/", 1)[-1]).title() if "/docs/" in issue else "Current issue"
    feat = "".join(f"<li>{file_link(l, u)}</li>" for l, u in ARTICLES["featured"])
    years = "".join(f'<h3 id="y{y}">{y}</h3><ul class="files cols">' + "".join(f"<li>{file_link(l, u)}</li>" for l, u in arts) + "</ul>"
                    for y, arts in sorted(ARTICLES["years"].items(), reverse=True))
    fam = "".join(f"<li>{file_link(l, u)}</li>" for l, u in ARTICLES["famous"])
    mag = (f'<div class="mag"><a class="mag-cover" href="{e(issue)}" rel="noopener">'
           + (f'<img src="{e(cover)}" alt="Cover of the {e(name)} of Knight Templar magazine" width="320" height="414">' if cover else "")
           + f'</a><div><p class="kicker">Now reading</p><h2>{e(name)}</h2>'
           f'<p>Knight Templar is the Grand Encampment\'s magazine for every Sir Knight, with Templar history, news from the Grand Master and Grand Commanderies, and the monthly State News.</p>'
           f'<p class="btns"><a class="btn" href="{e(issue)}" rel="noopener">{icon("book")} Read this issue</a>'
           f'<a class="btn btn-quiet" href="{ISSUU}" rel="noopener">All issues on Issuu</a></p>'
           f'<p class="apps">Read it on your phone: <a href="{APPLE}" rel="noopener">Apple App Store</a> · <a href="{ANDROID}" rel="noopener">Google Play</a></p></div></div>')
    body = (hero("Knight Templar magazine", "The magazine of the Grand Encampment, published since 1955.", "Publications")
            + f'<div class="wrap">{mag}<h2>Featured articles</h2><ul class="files cols">{feat}</ul>'
            f'<p><a class="btn btn-quiet" href="/magazine/articles/">Article library, 2007–2015</a> <a class="btn btn-quiet" href="/magazine/famous-masons/">Famous Masons</a> <a class="btn btn-quiet" href="/news/">State News</a></p></div>')
    write("/magazine/", page("/magazine/", "Knight Templar magazine", body, "Read the current Knight Templar magazine and the article library."))
    body = hero("Article library", "Articles from Knight Templar magazine, by year.", "Knight Templar magazine") + f'<div class="wrap prose-wide"><h2>Featured</h2><ul class="files cols">{feat}</ul>{years}</div>'
    write("/magazine/articles/", page("/magazine/articles/", "Article library", body, crumbs=[("/magazine/", "Magazine")]))
    body = hero("Famous Masons", "Articles from Knight Templar magazine about well-known Freemasons.", "Knight Templar magazine") + f'<div class="wrap"><ul class="files cols">{fam}</ul></div>'
    write("/magazine/famous-masons/", page("/magazine/famous-masons/", "Famous Masons", body, crumbs=[("/magazine/", "Magazine")]))


def notice_groups():
    """Group home-page PDFs into the Easter and Christmas notices."""
    easter, xmas = [], []
    for label, url in HOME.get("notices", []):
        if "Easter" in url:
            easter.append((label, url))
        elif "Christmas" in url:
            xmas.append((label, url))
    return easter, xmas


def build_home(up):
    easter, xmas = notice_groups()
    ey = re.search(r"/(\d{4})_GEKT_Easter", " ".join(u for _, u in easter))
    year, latest = latest_news(8)
    news = "".join(f'<li><a href="{e(u)}" rel="noopener"><span class="st">{e(s)}</span><span class="mo">{e(m)} {year}</span></a></li>' for _, s, m, u in latest)
    nxt = "".join(event_card(x, True) for x in up[:4])
    cover = HOME.get("issue_cover")
    issue = HOME.get("issue") or ISSUU
    body = f"""
<section class="hero hero-home">
<div class="wrap hero-grid">
<div>
<p class="kicker">Grand Encampment of Knights Templar of the U.S.A.</p>
<h1>Every Christian Mason should be a Knight Templar.</h1>
<p class="lede">The Grand Encampment gives every Christian Freemason the opportunity to extend his Masonic journey through the chivalric experience: in the Commandery, in service to its charities, and in fellowship with Sir Knights across the world.</p>
<p class="btns"><a class="btn" href="/about/join/">How to become a Knight Templar</a><a class="btn btn-quiet" href="/resources/grand-commanderies/">Find your Grand Commandery</a></p>
</div>
<img class="hero-seal" src="/img/seal.webp" alt="Seal of the Grand Encampment of Knights Templar of the U.S.A." width="360" height="360">
</div>
</section>
<div class="wrap">
<section class="notices" aria-labelledby="n-h">
<h2 id="n-h" class="vh">Notices</h2>
{f'''<article class="notice"><p class="kicker">Easter {ey.group(1) if ey else ""}</p><h3>97th Annual Easter Observance</h3><p>Sunrise service on the steps of the George Washington Masonic National Memorial, Alexandria, Virginia, on Easter Sunday, March 28, 2027. Hotel and meal ticket cutoff: March 1, 2027.</p><ul class="files">{"".join(f"<li>{file_link(l, u)}</li>" for l, u in easter)}</ul></article>''' if easter else ""}
{f'''<article class="notice"><p class="kicker">Christmas</p><h3>Christmas Observance toast</h3><p>The toast to the Grand Master and the Grand Master's response, for Commanderies to read at their Christmas Observances.</p><ul class="files">{"".join(f"<li>{file_link(l, u)}</li>" for l, u in xmas)}</ul></article>''' if xmas else ""}
<article class="notice"><p class="kicker">August 12–18, 2027</p><h3>70th Triennial Conclave</h3><p>Burbank, California. Registration, hotel and program details are on the Triennial Conclave website.</p><ul class="files"><li>{file_link("kt-triennial.org", TRIENNIAL)}</li></ul></article>
</section>
<section class="split">
<div>
<div class="sec-head"><h2>Coming up</h2><a href="/calendar/">Full calendar {icon("arrow", 16)}</a></div>
<div class="ev-list">{nxt or "<p>No upcoming events posted.</p>"}</div>
<p><a class="btn btn-quiet" href="/calendar.ics">{icon("cal")} Add these events to your calendar</a></p>
</div>
<div>
<div class="sec-head"><h2>Knight Templar magazine</h2><a href="/magazine/">More {icon("arrow", 16)}</a></div>
<a class="mag-home" href="{e(issue)}" rel="noopener">{f'<img src="{e(cover)}" alt="Cover of the current Knight Templar magazine" width="240" height="310" loading="lazy">' if cover else ""}<span>Read the current issue</span></a>
</div>
</section>
<section>
<div class="sec-head"><h2>Latest State News</h2><a href="/news/">Every state {icon("arrow", 16)}</a></div>
<ul class="news-grid">{news}</ul>
</section>
<section class="band leader">
<img src="/img/gekt/kussman.webp" alt="Sir Knight David J. Kussman" width="160" height="240" loading="lazy">
<div><p class="kicker">Most Eminent Grand Master</p><h2>Sir Knight David J. Kussman</h2>
<p>The Grand Master leads the Grand Encampment with the elected Grand Officers and the Department Commanders, who represent him across the United States and abroad.</p>
<p class="btns"><a class="btn" href="/leadership/grand-officers/">Grand Officers</a><a class="btn btn-quiet" href="/leadership/department-commanders/">Department Commanders</a></p></div>
</section>
<section>
<div class="sec-head"><h2>Knights Templar serve mankind</h2><a href="/charities/">Charities {icon("arrow", 16)}</a></div>
<ul class="charity">
<li><a href="https://www.ktef.org/" rel="noopener"><img src="/img/gekt/ktef.webp" alt="" width="120" height="120" loading="lazy"><span>Knights Templar Eye Foundation</span></a></li>
<li><a href="/charities/educational-foundation/"><img src="/img/gekt/ktedu.webp" alt="" width="120" height="120" loading="lazy"><span>Knights Templar Educational Foundation</span></a></li>
<li><a href="https://kthlp.com/" rel="noopener"><img src="/img/gekt/kthlp.webp" alt="" width="120" height="118" loading="lazy"><span>Holy Land Pilgrimage</span></a></li>
<li><a href="/charities/40-mile-project/"><img src="/img/gekt/40miles.webp" alt="" width="120" height="120" loading="lazy"><span>40 Mile Project prayer requests</span></a></li>
</ul>
</section>
<section class="split">
<div class="band"><p class="kicker">Education</p><h2>Templar Education Portal</h2><p>Online courses for Sir Knights, including Templar Ritualist, the History of the Medieval Knights Templar and the Commissioned Templar Chaplain program.</p><p><a class="btn" href="{EDUCATION}" rel="noopener">Browse courses</a></p></div>
<div class="band"><p class="kicker">Leadership</p><h2>York Rite Leadership Program</h2><p>Self improvement, understanding others and powerful communication: training that builds teams and empowers leaders in the Commandery and beyond.</p><p><a class="btn" href="https://yorkriteleadership.org/" rel="noopener">Learn more</a></p></div>
</section>
</div>
"""
    write("/", page("/", NAME, body, "The Grand Encampment of Knights Templar of the U.S.A.: how to join, the calendar, State News, Knight Templar magazine, leadership and charities."))


def build_contact():
    body = (hero("Contact", "The Grand Recorder's office handles membership questions, records and orders.", "Grand Encampment")
            + f"""<div class="wrap split">
<div class="band">
<h2>Grand Recorder's office</h2>
<p>{ADDRESS[0]}<br>{ADDRESS[1]}</p>
<p>{icon("phone", 16)} <a href="tel:+1{PHONE.replace('-', '')}">{PHONE}</a><br>Fax {FAX}<br>{icon("mail", 16)} <a href="mailto:{EMAIL}">{EMAIL}</a></p>
<p>The Grand Encampment's contact form is on <a href="{SRC}/contact/" rel="noopener">usagekt.org</a>.</p>
</div>
<div>
<h2>Looking for something else?</h2>
<ul class="link-list">
<li><a href="/about/join/">How to become a Knight Templar</a></li>
<li><a href="/resources/grand-commanderies/">Your Grand Commandery's website</a></li>
<li><a href="/leadership/grand-officers/">Email a Grand Officer</a></li>
<li><a href="/charities/40-mile-project/">Ask for prayer (40 Mile Project)</a></li>
<li><a href="/news/criteria/">Submit State News</a></li>
</ul>
</div>
</div>""")
    write("/contact/", page("/contact/", "Contact", body, "Contact the Grand Recorder's office of the Grand Encampment of Knights Templar."))


def build_demo_page():
    body = (hero("About this demonstration", "What this site is, and what it would take to make it the real one.", "knightstemplar.dev")
            + f"""<div class="wrap prose">
<p>This is a working demonstration of a new website for the Grand Encampment of Knights Templar of the U.S.A. It is not an official Grand Encampment site. Every page is built from content the Grand Encampment already publishes on <a href="{SRC}/" rel="noopener">usagekt.org</a>, so you can judge the design with your own words, officers and documents in it.</p>
<h2>What is different</h2>
<ul>
<li><strong>It keeps itself current.</strong> Each day it reads the usagekt.org calendar, State News and notices and rebuilds. Nobody has to post anything twice.</li>
<li><strong>A calendar you can subscribe to.</strong> Events, including dates announced in notices and on the Department Conferences page, are in one list and in a feed that Google, Apple and Outlook calendars can follow.</li>
<li><strong>State News by state.</strong> Every Grand Commandery's supplements in one searchable table, with the archive back to 2020.</li>
<li><strong>Fast and easy to read.</strong> Plain pages with no page builder, readable on a phone, in light or dark mode, and built to meet accessibility standards (WCAG 2.2 AA).</li>
<li><strong>Low cost and secure.</strong> Static pages served by Cloudflare: nothing to patch and nothing to hack.</li>
</ul>
<h2>What stays the same</h2>
<p>Members' logins, forms, documents and the magazine stay where they are today. The site links to them; nothing is moved.</p>
<p class="src-note">Built by <a href="https://creativetechnologypartners.com" rel="noopener">Creative Technology Partners</a>. Content last refreshed from usagekt.org on {UPDATED}.</p>
</div>""")
    write("/about-this-demo/", page("/about-this-demo/", "About this demonstration", body, "About the knightstemplar.dev demonstration site."))


def build_404():
    body = hero("Page not found", "That page isn't here. Try the menu above, or start from the home page.") + '<div class="wrap"><img class="knight-404" src="/img/gekt/knight-shield.webp" alt="" width="196" height="400"><p><a class="btn" href="/">Home</a></p></div>'
    (ROOT / "404.html").write_text(HOTLINK_IMG.sub("", page("/404", "Page not found", body)))


# Old knightstemplar.dev WordPress paths -> new pages.
OLD = {
    "/2024-easter-observance/": "/calendar/", "/69th-triennial/": "/history/triennial-conclaves/",
    "/charity/": "/charities/", "/charity/kt-educational-foundation/": "/charities/educational-foundation/",
    "/charity/kt-eye-foundation/": "https://www.ktef.org/", "/charity/kt-holy-land-pilgrimage/": "https://kthlp.com/",
    "/chivalric-orders/": "/about/orders/", "/department-conferences/": "/calendar/department-conferences/",
    "/history/conclaves/": "/history/triennial-conclaves/", "/history/the-order-today/": "/about/who-we-are/",
    "/leadership/aides/": "/leadership/aides/", "/leadership/college-of-honors/": "/leadership/college-of-honors/",
    "/leadership/commandery-directory/": "/resources/grand-commanderies/",
    "/leadership/committees-special/": "/leadership/committees/", "/leadership/committees-standing/": "/leadership/committees/",
    "/leadership/department-commanders/asia-pacific/": "/leadership/department-commanders/",
    "/leadership/department-commanders/east-central/": "/leadership/department-commanders/",
    "/leadership/department-commanders/europe-africa/": "/leadership/department-commanders/",
    "/leadership/department-commanders/latin-america/": "/leadership/department-commanders/",
    "/leadership/department-commanders/mid-atlantic/": "/leadership/department-commanders/",
    "/leadership/department-commanders/north-central/": "/leadership/department-commanders/",
    "/leadership/department-commanders/northeastern/": "/leadership/department-commanders/",
    "/leadership/department-commanders/northwestern/": "/leadership/department-commanders/",
    "/leadership/department-commanders/south-central/": "/leadership/department-commanders/",
    "/leadership/department-commanders/southeastern/": "/leadership/department-commanders/",
    "/leadership/department-commanders/southwestern/": "/leadership/department-commanders/",
    "/leadership/grand-master/": "/leadership/grand-officers/", "/leadership/deputy-grand-master/": "/leadership/grand-officers/",
    "/leadership/grand-captain-general/": "/leadership/grand-officers/", "/leadership/grand-generalissimo/": "/leadership/grand-officers/",
    "/leadership/grand-prelate/": "/leadership/grand-officers/", "/leadership/grand-recorder/": "/leadership/grand-officers/",
    "/leadership/grand-treasurer/": "/leadership/grand-officers/",
    "/leadership/past-grand-masters/": "/leadership/past-grand-officers/grand-masters/",
    "/leadership/pgm-2003-2006/": "/leadership/living-past-grand-masters/",
    "/leadership/pgm-2007-2012/": "/leadership/living-past-grand-masters/",
    "/leadership/pgm-2012-2015/": "/leadership/living-past-grand-masters/",
    "/leadership/pgm-2015-2018/": "/leadership/living-past-grand-masters/",
    "/leadership/pgm-2018-2021/": "/leadership/living-past-grand-masters/",
    "/resources/archive/": "/resources/", "/resources/awards/": "/history/awards-and-honors/",
    "/resources/commissioned-templar-chaplain/": "/resources/", "/resources/drill-team/": "/resources/drill-team/",
    "/resources/general-orders/": "/leadership/bulletins/", "/resources/in-memoriam/": "/leadership/",
    "/resources/masonic-links/": "/about/appendant-bodies/", "/resources/membership/": "/about/join/",
    "/resources/prayer-request/": "/charities/40-mile-project/", "/resources/presentations/": "/resources/",
    "/resources/websites-by-state/": "/resources/grand-commanderies/", "/resources/york-rite-leadership/": "/resources/",
    "/uniforms/": "/resources/uniforms-and-regalia/", "/visits/": "/leadership/visits/",
    "/wp-admin/*": "/", "/wp-login.php": "/", "/feed/*": "/calendar.ics",
}


def main():
    for p in ROOT.iterdir():
        if p.is_dir() and p.name not in ("img", "fonts"):
            shutil.rmtree(p)
    for slug, p in PAGES.items():
        PAGES_TITLE[TITLES.get(slug, "")] = p["title"]
    build_content_pages()
    build_sections()
    evs = all_events()
    up = build_calendar(evs)
    build_news()
    build_magazine()
    build_contact()
    build_demo_page()
    build_home(up)
    build_404()
    lines = [f"{old} {new} 301" for old, new in OLD.items() if old.rstrip("/*") != new.rstrip("/")]
    lines += [f"/{slug}/ {LOCAL[slug]} 301" for slug in sorted(LOCAL) if slug and not LOCAL[slug].startswith(f"/{slug}/") and "#" not in LOCAL[slug]]
    (ROOT / "_redirects").write_text("# Old knightstemplar.dev WordPress and usagekt.org paths. Generated by build/build.py.\n" + "\n".join(dict.fromkeys(lines)) + "\n")
    (ROOT / "_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n\n/calendar.ics\n  Content-Type: text/calendar; charset=utf-8\n  Cache-Control: public, max-age=3600\n")
    (ROOT / "robots.txt").write_text("# Demonstration site: keep it out of search engines.\nUser-agent: *\nDisallow: /\n")
    n = sum(1 for _ in ROOT.rglob("index.html"))
    print(f"Built {n} pages, {len(evs)} events ({len(up)} upcoming).")


if __name__ == "__main__":
    main()
