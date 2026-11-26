# reza-skandari.github.io

Personal academic website. Plain HTML and CSS, styled after the payslip-downloader page (same palette, fonts and light/dark modes).

## Layout

- `src/*.html`: page content only. The first line of each file is `<!-- title: Page name -->`.
- `data/publications.bib`, `data/preprints.bib`: the **public** bibliography. These files must never contain roles, collaboration notes, citation counts or trainee markers. Do not copy them from the promotion supplement's `references/` folder, which holds confidential annotations.
- `assets/`: `style.css`, `theme.js` (light/dark toggle) and `photo.jpg`.
- `build.py`: wraps every page in the shared header, navigation and footer, and generates `publications.html` from the `.bib` files.
- `docs/`: the built site. GitHub Pages serves this folder. Do not edit files here, because the build overwrites them.

## Update

1. Edit a page in `src/` or an entry in `data/*.bib`.
2. Run `python3 build.py`.
3. Open `docs/index.html` in a browser to check the result.

## Publishing (not yet done)

1. Create the public repository `reza-skandari.github.io`.
2. Push this folder to it.
3. In the repository's Pages settings, choose branch `main` and folder `/docs`.

The site will then be live at https://reza-skandari.github.io/.

## Content rule

Publish only official or publicly verifiable information. Leave out self-described roles, supervision claims, informal titles, personal circumstances, grant amounts, unsuccessful bids, student feedback, and students' names without their consent.
