# SLR Research Assistant v2.0

An evidence-first workspace for systematic literature reviews, designed around transparent methods, traceable decisions, and human validation.

**Live frontend:** https://lamonecampa.github.io/slr-research-assistant/  
**Repository:** https://github.com/lamonecampa/slr-research-assistant

## What is included

### Review design
- Review type, reporting guideline, registration, review team and PICO/PICo/SPIDER/PEO/CIMO question framing
- Inclusion/exclusion criteria, year/language/study-type limits
- Reviewer configuration, conflict resolution, appraisal and synthesis method

### Search and identification
- Reproducible search log: exact query, database, date, year limits, filters and record count
- Backend connectors for OpenAlex and Crossref public metadata APIs
- Backend connector adapters for Elsevier Scopus Search API and Clarivate Web of Science API (require approved keys/entitlements)
- RIS, BibTeX, CSV and JSON import
- Duplicate candidate detection by DOI, normalized title and fuzzy title similarity; human resolution queue

### Screening
- Separate title/abstract and full-text stages
- Reviewer 1, Reviewer 2 and adjudicator decisions
- Disagreement/conflict status
- Exclusion rationale and notes
- Optional AI advisory screening through the secured backend; AI never auto-excludes a record

### Appraisal and synthesis
- Appraisal register with tool, reviewer, overall judgment, domain judgments and evidence locator
- Extraction codebook for aim, method, context, technology, dataset, outcomes, findings, limitations, gaps and evidence locators
- Thematic register, research-gap register and AI-assisted narrative synthesis draft
- Evidence traceability fields and cautious output instructions

### Journal publication workspace
- Target-journal profile: journal name, SINTA 1/2/3 target, scope, author-guideline URL, article type, citation style and word limits
- Structured manuscript editor: title, abstract, keywords, Introduction, Methods, Results, Discussion, Conclusion and declarations
- Evidence-to-claim ledger for source-level traceability and page/table/figure locators
- Crossref DOI resolution and metadata comparison for DOI-bearing references
- Rule-based pre-submission completeness audit with actionable gaps; it is not an acceptance predictor or SINTA score
- Editable journal formatting profile: font, size, spacing, margins, alignment, headings, abstract and reference spacing\n- Formatted DOCX export using the saved profile, with local browser generation

### Reporting and export
- PRISMA 2020 count fields with arithmetic consistency checks
- PRISMA-style SVG flow export
- 27-item PRISMA 2020 reporting checklist tracker
- JSON project backup and CSV exports for records, search log, extraction matrix and checklist

## Architecture

- Frontend: static HTML, CSS and JavaScript; deployable with GitHub Pages.
- Backend: FastAPI + httpx + OpenAI Python SDK.
- AI: OpenAI Responses API, configured server-side.
- Metadata: OpenAlex and Crossref; Scopus and Web of Science connectors require provider API entitlements.

## Frontend deployment (GitHub Pages)

1. Open repository **Settings → Pages**.
2. Select **Deploy from a branch**.
3. Branch: `main`; folder: `/(root)`.
4. Save and wait for the Pages build.
5. Open the live frontend URL above.

## Backend deployment

The backend is separate from GitHub Pages. It must be deployed to a server/container host that supports Python.

1. Deploy the `backend/` directory as a Python service or Docker container.
2. Install dependencies from `backend/requirements.txt`.
3. Set environment variables from `backend/.env.example` in the hosting provider's secret manager.
4. Set `CORS_ORIGINS=https://lamonecampa.github.io` (add local development origin only when needed).
5. Set the frontend **Backend API base URL** in Integrations.
6. Test `GET /health`.

Example local run:

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Copy `.env.example` to `.env` for local use and load it with your deployment environment manager. Do not commit the real `.env`.

## API configuration

- `OPENAI_API_KEY`: required for AI screening, extraction and synthesis. API usage is billed separately by OpenAI and is not included with a ChatGPT subscription.
- `OPENAI_MODEL`: model available to the API project (default configured in backend).
- `SCOPUS_API_KEY`: Elsevier API key with the applicable Scopus API entitlement.
- `WOS_API_KEY`: Clarivate Web of Science API key and applicable product entitlement.
- `OPENALEX_MAILTO`, `CROSSREF_MAILTO`: contact email for polite API use.
- `CORS_ORIGINS`: allowed frontend origins.

An API key alone does not guarantee entitlement to Scopus or Web of Science data. Confirm institutional access, API terms, quota and permitted use with the provider.

## Important methodological limitations

This release is a functional research-workflow prototype, not a validated replacement for a review methodologist, librarian, or independent reviewers.

- Browser data is stored in localStorage. It is local to that browser/device and is not a shared team database. Export JSON backups regularly.
- The backend does not yet provide user authentication, role-based access, cloud project persistence, audit-grade immutable logs, file/full-text storage, or production rate limiting.
- OpenAlex and Crossref search results are metadata discovery, not equivalent to Scopus/WoS coverage. Preserve original database exports and exact search strategies.
- Provider API response fields and access vary by subscription and API version; validate connector output before formal reporting.
- AI screening/extraction/synthesis only sees the metadata/abstract supplied by the frontend unless full-text processing is separately implemented. Verify all outputs against the original paper. AI recommendations must not independently exclude studies.
- The PRISMA flow panel provides arithmetic checks and a downloadable schematic. It does not automatically establish a PRISMA-compliant review; verify every count against search logs and full-text decisions. Reports and studies are different units.
- The manuscript editor is a structured drafting workspace. It does not autonomously produce a validated scholarly article; authors must write and verify every claim against source evidence. Markdown and formatted DOCX exports are available. DOCX formatting uses the user-entered journal profile; it does not import or reproduce an uploaded publisher DOCX template exactly. Users must verify every setting against the current author guidelines and inspect the generated file before submission.
- The appraisal form is configurable. It does not automatically implement scoring algorithms for JBI, CASP, MMAT, RoB 2, ROBINS-I, QUADAS-2 or AMSTAR 2. Use the official instrument and its domain-specific guidance.
- No statistical meta-analysis engine/effect-size calculator, GRADE/CERQual implementation, PDF full-text parser, or multi-user adjudication workflow is included yet. The DOCX generator applies configurable page and text styles but does not clone publisher-specific Word template internals, macros, section breaks, or complex table/figure layouts. DOI checks query Crossref from the browser and may not resolve DOIs absent from Crossref; compare all metadata against the publisher's version of record.

## Methodological references

- PRISMA 2020: https://www.prisma-statement.org/prisma-2020-statement
- PRISMA 2020 checklist: https://www.prisma-statement.org/prisma-2020-checklist
- PRISMA 2020 flow diagrams: https://www.prisma-statement.org/prisma-2020-flow-diagram
- PRISMA-S: https://www.prisma-statement.org/prisma-search
- Elsevier Scopus APIs: https://dev.elsevier.com/
- Clarivate Web of Science APIs: https://developer.clarivate.com/

## Security

Never place OpenAI, Scopus or Web of Science keys in frontend code, browser storage, committed configuration files, or public issues. Store them only as backend environment secrets. Configure HTTPS, authentication, authorization, rate limiting, request logging and backups before allowing a research team to use the service with non-public project data.

## License

No license has been selected. Add a license only after deciding the intended reuse and distribution terms.
