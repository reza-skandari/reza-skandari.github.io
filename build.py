#!/usr/bin/env python3
"""Build the static site into docs/ from the files in content/.

    content/site.toml         name, titles, links, About, interests, students
    content/research.toml     research themes and current directions
    content/impact.toml       guidelines, practice, recognition, media
    content/teaching.toml     modules, approach, awards
    content/talks.toml        invited talks, service, memberships
    content/publications.bib  journal articles (newest N shown on Home)
    content/preprints.bib     working papers (shown on Research)

Text fields accept [link text](https://...) for links and *text* for italics.
The .bib files are PUBLIC copies: never put roles, collaboration notes,
citation counts or trainee markers in them.

Usage:  python3 build.py
"""
import datetime
import html
import pathlib
import re
import shutil
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"
OUT = ROOT / "docs"
SITE_URL = "https://reza-skandari.github.io/"
MY_LAST = "Skandari"

NAV = [
    ("index.html", "Home"),
    ("research.html", "Research"),
    ("impact.html", "Impact"),
    ("teaching.html", "Teaching"),
    ("talks.html", "Talks & Service"),
]


def load(name):
    with open(CONTENT / f"{name}.toml", "rb") as f:
        return tomllib.load(f)


# ── Text helpers ─────────────────────────────────────────────────────────
def md(s):
    """Escape text, then allow [label](url), **bold** and *italic*."""
    links = []

    def keep(m):
        links.append((m.group(1), m.group(2)))
        return f"\x00{len(links) - 1}\x00"

    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", keep, s)
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    return re.sub(r"\x00(\d+)\x00",
                  lambda m: f'<a href="{html.escape(links[int(m.group(1))][1])}">'
                            f'{md(links[int(m.group(1))][0])}</a>', s)


def paragraphs(items):
    return "\n".join(f"<p>{md(p)}</p>" for p in items)


def item_list(items):
    """Items are strings, or tables with optional 'year', optional 'title', and 'text'."""
    lis = []
    for it in items:
        if isinstance(it, str):
            lis.append(f"<li>{md(it)}</li>")
            continue
        head = f'<span class="when">{html.escape(it["year"])}</span> &middot; ' if it.get("year") else ""
        title = f"<strong>{md(it['title'])}</strong> " if it.get("title") else ""
        lis.append(f"<li>{head}{title}{md(it['text'])}</li>")
    return '<ul class="plain">\n' + "\n".join(lis) + "\n</ul>"


def section(heading, body, sid=None):
    attr = f' id="{sid}"' if sid else ""
    return f'<section{attr}>\n<div class="section-label">{html.escape(heading)}</div>\n{body}\n</section>'


def page_head(eyebrow, heading, intro=None):
    out = f'<section>\n<div class="eyebrow">{html.escape(eyebrow)}</div>\n<h1>{html.escape(heading)}</h1>\n'
    if intro:
        out += f'<p class="muted" style="margin-top:10px">{md(intro)}</p>\n'
    return out + "</section>"


# ── Minimal BibTeX reader ────────────────────────────────────────────────
def read_bib(path):
    text = path.read_text(encoding="utf-8")
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        etype, key = m.group(1).lower(), m.group(2)
        i, depth = m.end(), 1
        while depth and i < len(text):
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        entries.append(dict(parse_fields(text[m.end():i - 1]), _type=etype, _key=key))
    return entries


def parse_fields(body):
    fields, i, n = {}, 0, len(body)
    field_re, bare_re = re.compile(r"\s*,?\s*(\w+)\s*=\s*"), re.compile(r"[^,\s]+")
    while i < n:
        m = field_re.match(body, i)
        if not m:
            break
        name, i = m.group(1).lower(), m.end()
        if i >= n:
            break
        if body[i] == "{":
            depth, j = 1, i + 1
            while depth and j < n:
                depth += {"{": 1, "}": -1}.get(body[j], 0)
                j += 1
            value, i = body[i + 1:j - 1], j
        elif body[i] == '"':
            j = body.index('"', i + 1)
            value, i = body[i + 1:j], j + 1
        else:
            m2 = bare_re.match(body, i)
            value, i = m2.group(0), m2.end()
        fields[name] = re.sub(r"\s+", " ", value).strip()
    return fields


def tex(s):
    """LaTeX field text to HTML."""
    links = []

    def keep(m):
        links.append((m.group(1), m.group(2)))
        return f"\x00{len(links) - 1}\x00"

    s = re.sub(r"\\href\{([^}]*)\}\{([^}]*)\}", keep, s)
    s = s.replace("\\&", "&")
    s = html.escape(s, quote=False)
    s = re.sub(r"\\(?:textit|emph)\{([^}]*)\}", r"<i>\1</i>", s)
    s = s.replace("``", "\u201c").replace("''", "\u201d").replace("`", "\u2018")
    s = s.replace("---", "\u2014").replace("--", "\u2013")
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\x00(\d+)\x00",
                  lambda m: f'<a href="{html.escape(links[int(m.group(1))][0])}">'
                            f'{tex(links[int(m.group(1))][1])}</a>', s)


def initials(given):
    out = []
    for p in re.split(r"[\s.]+", given.strip()):
        if not p:
            continue
        if p.isupper() and len(p) > 1 and "-" not in p:   # e.g. "RS"
            out.extend(c + "." for c in p)
        else:
            out.append(p[0] + ".")
    return " ".join(out)


def authors(field):
    names = []
    for a in field.split(" and "):
        a = a.replace("*", "").strip()
        if a == "others":
            names.append("et al.")
            continue
        if "," in a:
            last, given = [x.strip() for x in a.split(",", 1)]
        else:
            bits = a.split()
            last, given = bits[-1], " ".join(bits[:-1])
        last = last.strip("{}")
        name = f"{html.escape(last)}, {html.escape(initials(given))}".strip(", ")
        names.append(f'<span class="me">{name}</span>' if last == MY_LAST else name)
    if names and names[-1] == "et al.":
        return ", ".join(names[:-1]) + ", et al."
    if len(names) > 8:   # first six, my name if hidden, last author
        me = next((i for i, n in enumerate(names) if 'class="me"' in n), None)
        short = names[:6] + ["&hellip;"]
        if me is not None and 6 <= me < len(names) - 1:
            short += [names[me], "&hellip;"]
        names = short + [names[-1]]
    return ", ".join(names[:-1]) + (", & " if len(names) > 1 else "") + names[-1]


def pub_item(e, working=False):
    title = tex(e.get("title", "")).rstrip(".")
    if working:   # working papers: authors, year and title only, no links
        return f'<li>{authors(e.get("author", ""))} ({e.get("year", "")}). <span class="pub-title">{title}.</span></li>'

    parts = [f'{authors(e.get("author", ""))} ({e.get("year", "")}).',
             f'<span class="pub-title">{title}.</span>']
    venue = e.get("journal") or e.get("howpublished") or e.get("school")
    if venue:
        v = f"<i>{tex(venue)}</i>"
        if e.get("volume"):
            v += f', {tex(e["volume"])}' + (f'({tex(e["number"])})' if e.get("number") else "")
        if e.get("pages"):
            v += f', {tex(e["pages"])}'
        if e.get("note"):
            v += f'. {tex(e["note"])}'
        parts.append(f'<span class="pub-meta">{v}.</span>')
    out = " ".join(parts)
    if e.get("doi"):
        out += f' <span class="pub-links"><a href="https://doi.org/{html.escape(e["doi"])}">DOI</a></span>'
    elif e.get("url"):
        out += f' <span class="pub-links"><a href="{html.escape(e["url"])}">Preprint</a></span>'
    if e.get("addendum"):
        out += f'<div class="pub-note">{tex(e["addendum"])}</div>'
    return f"<li>{out}</li>"


def sort_key(e):
    year = int(re.sub(r"\D", "", e.get("year", "0")) or 0)
    month = int(re.sub(r"\D", "", e.get("month", "0")) or 0)
    return (-year, -month, e.get("title", ""))


def pub_list(entries, working=False):
    return '<ol class="pubs">\n' + "\n".join(pub_item(e, working) for e in entries) + "\n</ol>"


# ── Pages ────────────────────────────────────────────────────────────────
def home(site, research):
    photo = (f'<img src="assets/{site["photo"]}" srcset="assets/{site["photo"]} 1x, '
             f'assets/{site["photo_2x"]} 2x" width="170" height="212" alt="{html.escape(site["name"])}">')
    links = [f'<a href="mailto:{html.escape(site["email"])}">Email</a>'] + \
            [f'<a href="{html.escape(l["url"])}">{html.escape(l["label"])}</a>' for l in site["links"]]
    hero = (f'<section class="hero">\n  {photo}\n  <div>\n'
            f'    <h1>{html.escape(site["name"])}, {html.escape(site["degree"])}</h1>\n'
            f'    <p class="role">{"<br>".join(html.escape(t) for t in site["title_lines"])}</p>\n'
            f'    <div class="links">\n      ' + "\n      ".join(links) + "\n    </div>\n  </div>\n</section>")
    tags = '<ul class="tags">\n' + "\n".join(f"<li>{html.escape(t)}</li>" for t in site["interests"]) + "\n</ul>"
    cards = '<div class="cards">\n' + "\n".join(
        f'<div class="card"><h3>{html.escape(t["title"])}</h3><p>{md(t["card"])}</p></div>'
        for t in research["theme"]) + "\n</div>\n" \
        '<p class="small" style="margin-top:12px"><a href="research.html">More on my research &rarr;</a></p>'
    articles = [e for e in read_bib(CONTENT / "publications.bib") if e["_type"] == "article"]
    recent = sorted(articles, key=sort_key)[:site["recent_publications"]]
    pubs = pub_list(recent) + (f'\n<p class="small" style="margin-top:12px"><a href="{html.escape(site["full_publication_list"])}">'
                               "Full publication list on my Imperial profile &rarr;</a></p>")
    return "Home", "\n\n".join([
        hero,
        section("About", paragraphs(site["about"])),
        section("Research interests", tags),
        section("Research themes", cards),
        section("Recent publications", pubs, sid="publications"),
        section("Prospective PhD students", f"<p>{md(site['prospective_students'])}</p>"),
    ])


def research_page(site, research):
    def theme(t):
        apps = ""
        if t.get("applications"):
            apps = ('\n<div class="apps"><span class="apps-label">Applications</span>'
                    '<ul class="tags small-tags">' + "".join(f"<li>{html.escape(a)}</li>" for a in t["applications"])
                    + "</ul></div>")
        return f"<section>\n<h2>{html.escape(t['title'])}</h2>\n<p>{md(t['text'])}</p>{apps}\n</section>"
    themes = "\n\n".join(theme(t) for t in research["theme"])
    preprints = sorted(read_bib(CONTENT / "preprints.bib"), key=sort_key)
    note = (f'<p class="small">Recent publications are on the <a href="index.html#publications">home page</a>; '
            f'the full list is on my <a href="{html.escape(site["full_publication_list"])}">Imperial profile</a>.</p>')
    return "Research", "\n\n".join([
        page_head("Research", research["heading"], research["intro"]),
        themes,
        f"<section>\n<h2>Current directions</h2>\n{item_list(research['direction'])}\n</section>",
        f"<section>\n<h2>Working papers</h2>\n{pub_list(preprints, working=True)}\n</section>",
        note,
    ])


def impact_page(impact):
    blocks = [f"<section>\n<h2>{html.escape(s['title'])}</h2>\n{item_list(s['items'])}\n</section>"
              for s in impact["section"]]
    return "Impact", "\n\n".join([page_head("Impact", impact["heading"], impact["intro"])] + blocks)


def teaching_page(teaching):
    def modules(items):
        return '<ul class="plain">\n' + "\n".join(
            f'<li><strong>{md(m["name"])}</strong><br><span class="muted small">{md(m["programmes"])}</span></li>'
            for m in items) + "\n</ul>"
    parts = [page_head("Teaching", "Teaching", teaching["intro"]),
             f"<section>\n<h2>Current modules</h2>\n{modules(teaching['current'])}\n</section>"]
    if teaching.get("previous"):
        parts.append(f"<section>\n<h2>Previous modules</h2>\n{modules(teaching['previous'])}\n</section>")
    parts.append(f"<section>\n<h2>Approach</h2>\n{paragraphs(teaching['approach'])}\n</section>")
    if teaching.get("award"):
        parts.append(f"<section>\n<h2>Recognition</h2>\n{item_list(teaching['award'])}\n</section>")
    return "Teaching", "\n\n".join(parts)


def talks_page(talks):
    return "Talks & Service", "\n\n".join([
        page_head("Talks & service", "Talks and service"),
        f"<section>\n<h2>Invited talks</h2>\n{item_list(talks['talk'])}\n</section>",
        f"<section>\n<h2>Professional service</h2>\n{item_list(talks['service'])}\n</section>",
        f"<section>\n<h2>Memberships</h2>\n{item_list(talks['memberships'])}\n</section>",
    ])


# ── Layout ───────────────────────────────────────────────────────────────
TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | {name}</title>
<meta name="description" content="{description}">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:title" content="{name} | Health Analytics and Operations">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{site_url}assets/{photo_2x}">
<meta property="og:url" content="{site_url}{page}">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="assets/style.css">
<script src="assets/theme.js"></script>
</head>
<body>
<main class="page">
<header class="top-bar">
  <a class="brand" href="index.html">{name}</a>
  <div class="bar-actions">
    <button class="theme-toggle" type="button" aria-label="Switch colour theme" title="Switch colour theme"></button>
    <button class="menu-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="site-nav">&#9776;</button>
  </div>
  <nav id="site-nav">
{nav}
  </nav>
</header>
{content}
</main>
<footer>
  <span>&copy; {year} {name} &middot; {affiliation}</span>
  <span>Last updated {updated}</span>
</footer>
</body>
</html>
"""

REDIRECT = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Publications</title>
<meta http-equiv="refresh" content="0; url={url}">
<link rel="canonical" href="{url}">
</head><body><p>The full publication list is on the <a href="{url}">Imperial profile</a>.</p></body></html>
"""


def render(site, filename, title, content):
    nav = "\n".join(f'    <a href="{href}"{" class=\"active\"" if href == filename else ""}>{html.escape(label)}</a>'
                    for href, label in NAV)
    today = datetime.date.today()
    name = html.escape(site["name"])
    return TEMPLATE.format(
        title=html.escape(title), name=name, nav=nav, content=content,
        description=html.escape(", ".join([site["title_lines"][0]] + site["title_lines"][1:]) + "."),
        affiliation=html.escape(", ".join(site["title_lines"][1:])),
        site_url=SITE_URL, page="" if filename == "index.html" else filename,
        photo_2x=site["photo_2x"], year=today.year, updated=today.strftime("%B %Y"))


def main():
    site, research = load("site"), load("research")
    pages = {
        "index.html": home(site, research),
        "research.html": research_page(site, research),
        "impact.html": impact_page(load("impact")),
        "teaching.html": teaching_page(load("teaching")),
        "talks.html": talks_page(load("talks")),
    }
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    for filename, (title, content) in pages.items():
        (OUT / filename).write_text(render(site, filename, title, content), encoding="utf-8")
    # The old Publications page forwards to the full list, so shared links keep working.
    (OUT / "publications.html").write_text(REDIRECT.format(url=html.escape(site["full_publication_list"])),
                                           encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    print("Built:", ", ".join(sorted(pages)))


if __name__ == "__main__":
    main()
