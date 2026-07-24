#!/usr/bin/env python3
# Generate publications.html from references.bib
import re, html, sys

SITE = "/Users/jakobabeer/Sync/Jakob/Programming/Repositories/2027_academic_website"
BIB = SITE + "/references.bib"
OUT = SITE + "/publications.html"

text = open(BIB, encoding="mac_roman").read()

# ---- 1. Split into raw entries with brace matching ----
entries = []
i, n = 0, len(text)
while True:
    at = text.find("@", i)
    if at == -1:
        break
    m = re.match(r"@(\w+)\s*\{", text[at:])
    if not m:
        i = at + 1
        continue
    etype = m.group(1).lower()
    brace_start = at + m.end() - 1
    depth, j = 0, brace_start
    while j < n:
        c = text[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    raw = text[at:j + 1]
    body = text[brace_start + 1:j]
    entries.append((etype, raw, body))
    i = j + 1

# ---- 2. Parse fields ----
def parse_fields(body):
    key, _, rest = body.partition(",")
    fields = {}
    s, p, L = rest, 0, len(rest)
    while p < L:
        while p < L and s[p] in " \t\r\n,":
            p += 1
        st = p
        while p < L and (s[p].isalnum() or s[p] in "-_"):
            p += 1
        name = s[st:p].strip().lower()
        if not name:
            break
        while p < L and s[p] != "=":
            p += 1
        p += 1
        while p < L and s[p] in " \t\r\n":
            p += 1
        if p >= L:
            break
        if s[p] == "{":
            depth, vs = 0, p
            while p < L:
                if s[p] == "{":
                    depth += 1
                elif s[p] == "}":
                    depth -= 1
                    if depth == 0:
                        p += 1
                        break
                p += 1
            value = s[vs + 1:p - 1]
        elif s[p] == '"':
            vs = p + 1
            p += 1
            while p < L and s[p] != '"':
                p += 1
            value = s[vs:p]
            p += 1
        else:
            vs = p
            while p < L and s[p] not in ",\n":
                p += 1
            value = s[vs:p].strip()
        fields[name] = value
    return key.strip(), fields

# ---- 3. De-LaTeX for display ----
ACC = {
    r'{\ss}': 'ß', r'{\"a}': 'ä', r'{\"o}': 'ö', r'{\"u}': 'ü',
    r'{\"A}': 'Ä', r'{\"O}': 'Ö', r'{\"U}': 'Ü', r'{\ae}': 'æ',
    r'{\o}': 'ø', r'{\O}': 'Ø', r'{\aa}': 'å', r'{\AA}': 'Å',
    r"{\'e}": 'é', r"{\`e}": 'è', r"{\^e}": 'ê', r"{\'a}": 'á',
    r"{\'o}": 'ó', r"{\'i}": 'í', r"{\'\i}": 'í', r"{\'c}": 'ć',
    r"{\'n}": 'ń', r"{\v c}": 'č', r"{\v s}": 'š', r"{\c c}": 'ç',
    r"{\~n}": 'ñ', r"{\'u}": 'ú', r'{\"e}': 'ë', r'{\.z}': 'ż',
}
def delatex(x):
    if not x:
        return ""
    for k, v in ACC.items():
        x = x.replace(k, v)
    # bare accent forms e.g. \"a  \'e
    x = re.sub(r'\\"([aeiouAEIOU])', lambda m: {'a':'ä','e':'ë','i':'ï','o':'ö','u':'ü','A':'Ä','O':'Ö','U':'Ü'}.get(m.group(1), m.group(1)), x)
    x = re.sub(r"\\'([aeiouAEIOU])", lambda m: {'a':'á','e':'é','i':'í','o':'ó','u':'ú'}.get(m.group(1), m.group(1)), x)
    x = x.replace("\\&", "&").replace("~", " ")
    x = x.replace("{", "").replace("}", "")
    x = re.sub(r"\s+", " ", x).strip()
    return x

def fmt_authors(raw):
    if not raw:
        return ""
    people = [a.strip() for a in re.split(r"\s+and\s+", raw) if a.strip()]
    out = []
    for pers in people:
        if "," in pers:
            last, first = pers.split(",", 1)
            name = f"{first.strip()} {last.strip()}"
        else:
            name = pers
        out.append(delatex(name))
    if len(out) == 1:
        return out[0]
    return ", ".join(out[:-1]) + " & " + out[-1]

def pages(f):
    return f.get("pages", "").replace("--", "–")

# ---- 4. Categorise ----
CATS = [
    ("books", "Books & Edited Volumes"),
    ("chapters", "Book Chapters"),
    ("theses", "Theses"),
    ("articles", "Journal Articles"),
    ("conference", "Conference Papers"),
    ("preprints", "Preprints"),
]
buckets = {c[0]: [] for c in CATS}

def category(etype, f):
    if etype in ("book", "proceedings"):
        return "books"
    if etype in ("incollection", "inbook"):
        return "chapters"
    if etype in ("phdthesis", "mastersthesis"):
        return "theses"
    if etype == "article":
        jt = (f.get("journaltitle", "") + f.get("journal", "")).lower()
        if "arxiv" in jt or "preprint" in jt:
            return "preprints"
        return "articles"
    if etype in ("inproceedings", "conference"):
        return "conference"
    return None  # misc/techreport/etc -> skip

# ---- 5. Clean raw bibtex for copy (drop JabRef cruft) ----
def clean_raw(raw):
    lines = raw.split("\n")
    kept = [ln for ln in lines if not re.match(r"\s*(owner|timestamp|abstract|keywords|file|groups)\s*=", ln, re.I)]
    out = "\n".join(kept)
    out = re.sub(r",\s*\n\}", "\n}", out)   # fix dangling comma before close
    return out.strip()

# ---- 6. Build citation HTML per type ----
def esc(s):
    return html.escape(s or "")

def venue(etype, f):
    if etype == "article":
        return f.get("journaltitle") or f.get("journal") or ""
    if etype in ("inproceedings", "conference", "incollection", "inbook"):
        return f.get("booktitle", "")
    if etype == "proceedings":
        return f.get("publisher", "") or f.get("organization", "")
    if etype in ("phdthesis", "mastersthesis"):
        return f.get("school", "")
    if etype == "book":
        return f.get("publisher", "")
    return ""

def citation(etype, key, f):
    authors = fmt_authors(f.get("author", "")) or fmt_authors(f.get("editor", ""))
    editors_only = not f.get("author") and f.get("editor")
    title = delatex(f.get("title", ""))
    yr = f.get("year", "")
    v = delatex(venue(etype, f))
    bits = []
    if authors:
        bits.append(esc(authors) + ("&nbsp;(eds.)" if editors_only else "") + ".")
    bits.append(f"<strong>{esc(title)}.</strong>")
    tail = []
    if etype in ("phdthesis", "mastersthesis"):
        kind = "PhD thesis" if etype == "phdthesis" else "Master's thesis"
        seg = kind + (", " + esc(v) if v else "")
        tail.append(seg)
    else:
        if v:
            tail.append(f'<span class="venue">{esc(v)}</span>')
        vol = f.get("volume", "")
        num = f.get("number", "")
        pg = pages(f)
        volnum = ""
        if vol:
            volnum = esc(vol) + (f"({esc(num)})" if num else "")
        if volnum and pg:
            tail.append(volnum + ":" + esc(pg))
        elif volnum:
            tail.append(volnum)
        elif pg:
            tail.append("pp. " + esc(pg))
    joined = ", ".join(t for t in tail if t)
    if joined:
        bits.append(joined + (", " if yr else "") + esc(yr) + ".")
    elif yr:
        bits.append(esc(yr) + ".")
    line = " ".join(bits)
    doi = f.get("doi", "")
    url = f.get("url", "")
    if doi:
        line += f' <a href="https://doi.org/{esc(doi)}">doi</a>'
    elif url:
        line += f' <a href="{esc(url)}">link</a>'
    return authors, title, yr, line

# ---- 7. Populate buckets ----
seen = 0
skipped = []
submitted = []
for etype, raw, body in entries:
    key, f = parse_fields(body)
    venue_txt = " ".join([f.get("journaltitle", ""), f.get("journal", ""),
                          f.get("booktitle", "")]).lower()
    if "submitted to" in venue_txt:          # exclude manuscripts under review
        submitted.append((etype, key))
        continue
    cat = category(etype, f)
    if cat is None:
        skipped.append((etype, key))
        continue
    authors, title, yr, line = citation(etype, key, f)
    try:
        y = int(re.search(r"\d{4}", yr).group()) if yr else 0
    except Exception:
        y = 0
    buckets[cat].append((y, title.lower(), line, clean_raw(raw)))
    seen += 1

for c in buckets:
    buckets[c].sort(key=lambda e: (-e[0], e[1]))

# ---- 8. Emit HTML ----
NAV = '''  <nav class="site-nav">
    <div class="nav-inner">
      <a class="brand" href="index.html">Jakob Abeßer</a>
      <a href="index.html">Home</a>
      <a class="active" href="publications.html">Publications</a>
      <a href="talks.html">Talks</a>
      <a href="teaching.html">Teaching</a>
      <a href="cv.html">CV</a>
    </div>
  </nav>'''

parts = []
parts.append('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Jakob Abeßer — Publications</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
''')
parts.append(NAV)
parts.append('''
  <main>
    <h1>Publications</h1>
    <p>
      Grouped by type, newest first. Click <span class="bib-link">bib</span> under any entry
      for its BibTeX. For the complete record see my
      <a href="#">Google Scholar</a> and <a href="https://orcid.org/0000-0003-4689-7944">ORCID</a> profiles.
    </p>
''')

bid = 0
for cslug, cname in CATS:
    items = buckets[cslug]
    if not items:
        continue
    parts.append(f'\n    <h2>{html.escape(cname)}</h2>\n    <ul class="pub-list">')
    for y, tl, line, raw in items:
        bid += 1
        code = esc(raw)
        parts.append(f'''
      <li>
        <div class="pub-cite">{line}</div>
        <div class="bib-row">
          <a class="bib-link" role="button" tabindex="0" onclick="toggleBib('bib{bid}')" onkeydown="if(event.key==='Enter'||event.key===' '){{toggleBib('bib{bid}');event.preventDefault();}}">bib</a>
        </div>
        <div class="bib-wrap" id="bib{bid}" hidden>
          <button class="copy-btn" onclick="copyBib(this,'code{bid}')">copy</button>
          <pre class="bib-code" id="code{bid}">{code}</pre>
        </div>
      </li>''')
    parts.append('\n    </ul>')

parts.append('''
  </main>

  <footer>© <span id="year"></span> Jakob Abeßer.</footer>

  <script>
    function toggleBib(id){
      var el = document.getElementById(id);
      el.hidden = !el.hidden;
    }
    function copyBib(btn, codeId){
      var txt = document.getElementById(codeId).textContent;
      navigator.clipboard.writeText(txt).then(function(){
        var old = btn.textContent;
        btn.textContent = 'copied';
        setTimeout(function(){ btn.textContent = old; }, 1200);
      });
    }
    document.getElementById('year').textContent = new Date().getFullYear();
  </script>

</body>
</html>
''')

open(OUT, "w", encoding="utf-8").write("".join(parts))

# ---- report ----
print("parsed entries:", len(entries), " included:", seen)
for cslug, cname in CATS:
    print(f"  {cname}: {len(buckets[cslug])}")
if skipped:
    print("skipped (type):", skipped)
if submitted:
    print("excluded (submitted to):", submitted)
