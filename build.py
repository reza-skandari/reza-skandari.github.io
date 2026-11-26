#!/usr/bin/env python3
"""Build the static site into docs/.

Pages live in src/*.html (content only; the first line is <!-- title: X -->).
The publications page is generated from data/publications.bib and
data/preprints.bib, which are PUBLIC copies: no roles, collaboration notes,
citation counts or trainee markers. Never point this at the promotion files.

Usage:  python3 build.py
"""
import datetime
import html
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "docs"
MY_LAST = "Skandari"

NAV = [
    ("index.html", "Home"),
    ("research.html", "Research"),
    ("publications.html", "Publications"),
    ("impact.html", "Impact"),
    ("teaching.html", "Teaching"),
    ("talks.html", "Talks & Service"),
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Reza Skandari</title>
<meta name="description" content="Reza Skandari, Assistant Professor of Health Analytics and Operations, Imperial Business School, Imperial College London.">
<link rel="stylesheet" href="assets/style.css">
<script src="assets/theme.js"></script>
</head>
<body>
<main class="page">
<header class="top-bar">
  <a class="brand" href="index.html">Reza Skandari</a>
  <nav>
{nav}
    <button class="theme-toggle" type="button" aria-label="Switch colour theme">Dark mode</button>
  </nav>
</header>
{content}
</main>
<footer>
  <span>&copy; {year} Reza Skandari &middot; Imperial Business School, Imperial College London</span>
  <span>Last updated {updated}</span>
</footer>
</body>
</html>
"""


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
        body = text[m.end():i - 1]
        entries.append(dict(parse_fields(body), _type=etype, _key=key))
    return entries


def parse_fields(body):
    fields, i, n = {}, 0, len(body)
    while i < n:
        m = re.compile(r"\s*,?\s*(\w+)\s*=\s*").match(body, i)
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
            m2 = re.compile(r"[^,\s]+").match(body, i)
            value, i = m2.group(0), m2.end()
        fields[name] = re.sub(r"\s+", " ", value).strip()
    return fields


# ── LaTeX → HTML ─────────────────────────────────────────────────────────
def tex(s):
    links = []

    def keep_link(m):
        links.append((m.group(1), m.group(2)))
        return f"\x00{len(links) - 1}\x00"

    s = re.sub(r"\\href\{([^}]*)\}\{([^}]*)\}", keep_link, s)
    s = s.replace("\\&", "&")
    s = html.escape(s, quote=False)
    s = re.sub(r"\\(?:textit|emph)\{([^}]*)\}", r"<i>\1</i>", s)
    s = s.replace("``", "\u201c").replace("''", "\u201d").replace("`", "\u2018")
    s = s.replace("---", "\u2014").replace("--", "\u2013")
    s = s.replace("{", "").replace("}", "")

    def put_link(m):
        url, label = links[int(m.group(1))]
        return f'<a href="{html.escape(url)}">{tex(label)}</a>'

    return re.sub(r"\x00(\d+)\x00", put_link, s)


def initials(given):
    parts = re.split(r"[\s.]+", given.strip())
    out = []
    for p in parts:
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
    return ", ".join(names[:-1]) + (", & " if len(names) > 1 else "") + names[-1]


def pub_item(e):
    title = tex(e.get("title", "")).rstrip(".")
    parts = [f'{authors(e.get("author", ""))} ({e.get("year", "")}).',
             f'<span class="pub-title">{title}.</span>']
    venue = e.get("journal") or e.get("howpublished") or e.get("school")
    if venue:
        v = f"<i>{tex(venue)}</i>"
        if e.get("volume"):
            v += f', {tex(e["volume"])}'
            if e.get("number"):
                v += f'({tex(e["number"])})'
        if e.get("pages"):
            v += f', {tex(e["pages"])}'
        if e.get("note"):
            v += f'. {tex(e["note"])}'
        parts.append(f'<span class="pub-meta">{v}.</span>')
    links = []
    if e.get("doi"):
        links.append(f'<a href="https://doi.org/{html.escape(e["doi"])}">DOI</a>')
    elif e.get("url"):
        links.append(f'<a href="{html.escape(e["url"])}">Preprint</a>')
    out = " ".join(parts)
    if links:
        out += f' <span class="pub-links">{" ".join(links)}</span>'
    if e.get("addendum"):
        out += f'<div class="pub-note">{tex(e["addendum"])}</div>'
    return f"<li>{out}</li>"


def sort_key(e):
    return (-int(re.sub(r"\D", "", e.get("year", "0")) or 0), e.get("title", ""))


def publications_page():
    pubs = read_bib(ROOT / "data" / "publications.bib")
    pre = read_bib(ROOT / "data" / "preprints.bib")
    articles = sorted([e for e in pubs if e["_type"] == "article"], key=sort_key)
    theses = [e for e in pubs if e["_type"] == "thesis"]
    pre = sorted(pre, key=sort_key)

    def block(title, items):
        lis = "\n".join(pub_item(e) for e in items)
        return f"<section>\n<h2>{title}</h2>\n<ol class=\"pubs\">\n{lis}\n</ol>\n</section>"

    return "\n".join([
        "<!-- title: Publications -->",
        '<section>\n<div class="eyebrow">Publications</div>\n<h1>Publications</h1>\n'
        '<p class="muted" style="margin-top:10px">Authors are listed in the order published. '
        'For citation information, see my <a href="https://scholar.google.com/citations?user=1Xc--mwAAAAJ&amp;hl=en">Google Scholar profile</a>.</p>\n</section>',
        block("Journal articles", articles),
        block("Preprints and working papers", pre),
        block("Doctoral thesis", theses),
    ])


# ── Build ────────────────────────────────────────────────────────────────
def render(name, content):
    m = re.match(r"\s*<!--\s*title:\s*(.*?)\s*-->", content)
    title = m.group(1) if m else name
    body = content[m.end():] if m else content
    nav = "\n".join(
        f'    <a href="{href}"{" class=\"active\"" if href == name else ""}>{html.escape(label)}</a>'
        for href, label in NAV)
    today = datetime.date.today()
    return TEMPLATE.format(title=html.escape(title), nav=nav, content=body.strip(),
                           year=today.year, updated=today.strftime("%B %Y"))


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    for src in sorted((ROOT / "src").glob("*.html")):
        (OUT / src.name).write_text(render(src.name, src.read_text(encoding="utf-8")), encoding="utf-8")
    (OUT / "publications.html").write_text(render("publications.html", publications_page()), encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    print("Built:", ", ".join(sorted(p.name for p in OUT.glob("*.html"))))


if __name__ == "__main__":
    main()
