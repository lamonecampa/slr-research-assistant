# SLR Research Assistant

A lightweight browser-based workspace for Systematic Literature Review (SLR).

## Features
- Import bibliography metadata from RIS, BibTeX, and CSV
- Detect duplicate records using DOI or normalized title
- Preliminary descriptive mapping: publication year, languages, authors, keywords
- Rule-based screening suggestions with reviewer decisions and exclusion reasons
- Manual data extraction fields
- PRISMA-style count summary based on the current library
- CSV export
- Local browser storage (localStorage)

## Run locally
Open `index.html` in a modern browser.

## Deploy with GitHub Pages
1. Open repository **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select branch `main` and folder `/(root)`.
4. Save. GitHub will publish the site at `https://lamonecampa.github.io/slr-research-assistant/`.

## Important limitations
This is a front-end prototype. It does **not** currently include:
- A generative AI model or server-side AI integration
- Automated Scopus or Web of Science searches
- A validated PRISMA 2020 flow diagram generator with every required branch/reason category
- Shared multi-user storage, authentication, or cloud database

Screening recommendations are keyword rules only. They are not AI judgments and must not replace independent human review. The PRISMA panel is a simplified count summary, not a substitute for checking the official PRISMA 2020 flow-diagram template and reporting checklist.

## Next development steps
- Add a backend (for example FastAPI) and PostgreSQL
- Add secure server-side LLM integration; never expose API keys in browser code
- Add integrations with OpenAlex, Crossref, and permitted Scopus/WoS APIs
- Implement duplicate resolution with human confirmation and audit log
- Implement full PRISMA 2020 flow fields, including records sought/retrieved, reports assessed, and reasons for exclusion

## License
No license has been specified yet. Add a license before redistributing the project.
