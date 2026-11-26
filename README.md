# reza-skandari.github.io

Personal academic website, live at https://reza-skandari.github.io/.

## How to update the site

All content lives in `content/`. Edit a file, rebuild, and push:

```
python3 build.py
git add -A && git commit -m "Update site" && git push
```

GitHub Pages publishes the new version within about a minute.

| To change… | Edit |
|---|---|
| Name, titles, buttons, About, research interests, prospective-students text, number of recent papers | `content/site.toml` |
| Research themes (home cards and Research page), current directions | `content/research.toml` |
| Guidelines, practice, recognition, media | `content/impact.toml` |
| Modules, teaching approach, teaching awards | `content/teaching.toml` |
| Invited talks, professional service, memberships | `content/talks.toml` |
| Journal articles (the newest are shown on Home) | `content/publications.bib` |
| Working papers (shown on Research) | `content/preprints.bib` |
| Photo, colours, fonts | `assets/` (`headshot.jpg`, `headshot-2x.jpg`, `style.css`) |

### Writing text

- Links: `[link text](https://example.com)`
- Italics: `*text*`. Bold: `**text**`.
- In `.toml` files, keep text inside straight double quotes. To use a double quote inside the text, write `\"`.
- Lists of dated items, such as talks, use one `[[talk]]` block per item:

  ```toml
  [[talk]]
  year = "2027"
  text = "Bayes Business School, City St George's, University of London"
  ```

- Items appear in the order you write them.

### Adding a publication

Add a BibTeX entry to `content/publications.bib`; you can paste one from Google Scholar or the journal. The home page shows the newest ones automatically, sorted by year and then month, so include `month = {11}` to break ties within a year. An optional `addendum = {...}` adds a short note under the entry; use `\href{url}{text}` for links there.

## Layout

- `content/`: everything you edit.
- `assets/`: images, `style.css`, and `theme.js` (light/dark toggle and phone menu).
- `build.py`: turns `content/` into the pages in `docs/`.
- `docs/`: the built site that GitHub Pages serves. Don't edit it by hand, because each build overwrites it.

## Content rule

Publish only official or publicly verifiable information. Leave out self-described roles, supervision claims, informal titles, personal circumstances, grant amounts, unsuccessful bids, student feedback, and students' names without their consent. The `.bib` files here are public copies. Never copy in the promotion supplement's annotated `.bib` files, which contain role notes, citation counts and trainee markers.
