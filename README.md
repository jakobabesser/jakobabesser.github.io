# Academic website — Jakob Abeßer

A plain static website (HTML + one CSS file). No build step, no dependencies.
The structure follows a conventional academic homepage: Home, Publications,
Talks, Teaching, CV.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Homepage: intro, research summary, keywords, news, projects, profiles, contact |
| `publications.html` | Publication list (journals, books, selected conference papers) |
| `talks.html` | Invited talks / keynotes |
| `teaching.html` | Courses and thesis supervision |
| `cv.html` | Positions, education, service |
| `style.css` | Shared styling for all pages (edit colors at the top) |

## Editing

- All text lives directly in the `.html` files — open one and edit between the tags.
- To restyle the whole site, edit the color variables at the top of `style.css`
  (`--accent`, `--bg`, etc.). Dark mode is handled automatically.
- The navigation bar is duplicated at the top of every page. If you add/rename a
  page, update the `<nav>` block in **each** file (change which link has `class="active"`).
- Add a real portrait: `index.html` already references `photo.jpg`, so just drop a
  (square) `photo.jpg` into this folder.
- Search the files for `TODO` and `<!-- ... -->` comments — those mark spots to fill in
  (e.g. Google Scholar / ResearchGate / LinkedIn profile URLs, any 2024–2026 publications,
  and a `cv.pdf` to link from the CV page).

## Publications (generated from BibTeX)

`publications.html` is **generated** from `references.bib` — don't edit it by hand.
Entries are grouped by type (Books & Edited Volumes → Chapters → Theses → Journal
Articles → Conference Papers → Preprints), newest first, each with a **bib** toggle that
reveals the cleaned BibTeX and a copy button.

When you update `references.bib`, regenerate the page:

```
python3 build_publications.py
```

Notes: `owner`/`timestamp`/`abstract`/`keywords` fields are stripped from the copyable
BibTeX; arXiv entries are routed to a "Preprints" section; `@unpublished` entries and any
entry whose venue contains "submitted to" (manuscripts under review) are excluded.
Anything wrong on the page should be fixed in `references.bib`, then rebuilt.

## Preview locally

Just open `index.html` in a browser (double-click it). No server needed.
Optionally, from this folder: `python3 -m http.server 8000` then visit
`http://localhost:8000`.

## Deploy to the university server

Your institution typically gives you a web folder reachable via SFTP/SSH
(often called `public_html`, `www`, or similar). Upload **all files in this
folder** into it, keeping them together:

```
scp -r * user@server.uni-bamberg.de:~/public_html/
```

(Replace the host/path with what Bamberg's IT gives you.) Because everything is
relative, the site works identically whether it lives at a domain root or in a
sub-path like `.../~abesser/`.
