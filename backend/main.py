"""SLR Research Assistant API.
Run with: uvicorn main:app --host 0.0.0.0 --port 8000
Credentials must be configured as server environment variables. Never expose them to the browser.
"""
import json
import os
from typing import Any
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import OpenAI

APP_NAME = "SLR Research Assistant API"
AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-6")
OPENALEX_MAILTO = os.getenv("OPENALEX_MAILTO", "")
CROSSREF_MAILTO = os.getenv("CROSSREF_MAILTO", "")
SCOPUS_API_KEY = os.getenv("SCOPUS_API_KEY", "")
WOS_API_KEY = os.getenv("WOS_API_KEY", "")

app = FastAPI(title=APP_NAME, version="2.0.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=False,
    allow_methods=["GET", "POST"], allow_headers=["Content-Type"]
)

class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1500)
    from_year: int | None = Field(default=None, ge=1900, le=2100)
    to_year: int | None = Field(default=None, ge=1900, le=2100)
    limit: int = Field(default=50, ge=1, le=100)

class AIRecord(BaseModel):
    id: str
    title: str
    abstract: str = ""
    year: str = ""
    keywords: str = ""

class ScreenRequest(BaseModel):
    criteria: dict[str, Any] = {}
    records: list[AIRecord] = Field(min_length=1, max_length=40)

class ExtractRequest(BaseModel):
    record: dict[str, Any]

class SynthesisRequest(BaseModel):
    question: str = ""
    records: list[dict[str, Any]] = Field(min_length=1, max_length=80)

def openai_client():
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(503, "OPENAI_API_KEY is not configured on the server.")
    return OpenAI()

def output_text(response):
    text = getattr(response, "output_text", None)
    if text:
        return text
    chunks = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            if getattr(content, "type", "") == "output_text":
                chunks.append(content.text)
    return "\n".join(chunks)

def parse_json(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start:end+1])
        raise HTTPException(502, "AI returned a non-JSON response; retry or inspect model configuration.")

def year_filter(req):
    filters = []
    if req.from_year:
        filters.append(f"from_publication_date:{req.from_year}-01-01")
    if req.to_year:
        filters.append(f"to_publication_date:{req.to_year}-12-31")
    return ",".join(filters)

def normalize_openalex(work):
    authors = [a.get("author", {}).get("display_name", "") for a in work.get("authorships", [])]
    loc = work.get("primary_location") or {}
    source = (loc.get("source") or {}).get("display_name", "")
    return {
        "title": work.get("display_name", ""),
        "authors": "; ".join(x for x in authors if x),
        "year": work.get("publication_year", ""),
        "doi": (work.get("doi") or "").replace("https://doi.org/", ""),
        "abstract": "",
        "language": work.get("language", ""),
        "keywords": "; ".join(k.get("display_name", "") for k in work.get("keywords", [])),
        "source": source,
        "url": work.get("doi") or work.get("id", ""),
        "openalex_id": work.get("id", "")
    }

@app.get("/health")
def health():
    return {
        "status": "ok", "version": "2.0.0",
        "ai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "scopus_configured": bool(SCOPUS_API_KEY),
        "wos_configured": bool(WOS_API_KEY)
    }

@app.post("/api/search/openalex")
async def search_openalex(req: SearchRequest):
    params = {"search": req.query, "per-page": req.limit, "select": "id,doi,display_name,publication_year,authorships,primary_location,language,keywords"}
    filters = year_filter(req)
    if filters:
        params["filter"] = filters
    if OPENALEX_MAILTO:
        params["mailto"] = OPENALEX_MAILTO
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.get("https://api.openalex.org/works", params=params)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"OpenAlex request failed: {e}")
    data = r.json()
    return {"source": "OpenAlex", "count": data.get("meta", {}).get("count", 0),
            "records": [normalize_openalex(w) for w in data.get("results", [])]}

@app.post("/api/search/crossref")
async def search_crossref(req: SearchRequest):
    params = {"query": req.query, "rows": req.limit, "select": "DOI,title,author,published,abstract,container-title,type,URL"}
    filters = []
    if req.from_year: filters.append(f"from-pub-date:{req.from_year}-01-01")
    if req.to_year: filters.append(f"until-pub-date:{req.to_year}-12-31")
    if filters: params["filter"] = ",".join(filters)
    if CROSSREF_MAILTO: params["mailto"] = CROSSREF_MAILTO
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "SLRResearchAssistant/2.0"}) as client:
        try:
            r = await client.get("https://api.crossref.org/works", params=params)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Crossref request failed: {e}")
    items = r.json().get("message", {}).get("items", [])
    records = []
    for w in items:
        authors = [(" ".join([a.get("given", ""), a.get("family", "")])).strip() for a in w.get("author", [])]
        date_parts = (w.get("published", {}).get("date-parts") or [[None]])[0]
        records.append({
            "title": (w.get("title") or [""])[0], "authors": "; ".join(authors),
            "year": date_parts[0] if date_parts else "", "doi": w.get("DOI", ""),
            "abstract": w.get("abstract", ""), "language": w.get("language", ""),
            "keywords": "", "source": (w.get("container-title") or [""])[0],
            "url": w.get("URL", ""), "documentType": w.get("type", "")
        })
    return {"source": "Crossref", "count": len(records), "records": records}

@app.post("/api/search/scopus")
async def search_scopus(req: SearchRequest):
    if not SCOPUS_API_KEY:
        raise HTTPException(503, "SCOPUS_API_KEY is not configured.")
    params = {"query": req.query, "count": req.limit, "start": 0}
    if req.from_year and req.to_year:
        params["date"] = f"{req.from_year}-{req.to_year}"
    headers = {"X-ELS-APIKey": SCOPUS_API_KEY, "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=40) as client:
        try:
            r = await client.get("https://api.elsevier.com/content/search/scopus", params=params, headers=headers)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Scopus API request failed. Check key, entitlement, quota and query syntax: {e}")
    entries = r.json().get("search-results", {}).get("entry", [])
    records = []
    for x in entries:
        records.append({
            "title": x.get("dc:title", ""), "authors": x.get("dc:creator", ""),
            "year": x.get("prism:coverDate", "")[:4], "doi": x.get("prism:doi", ""),
            "abstract": "", "language": "", "keywords": "",
            "source": x.get("prism:publicationName", ""), "url": x.get("prism:url", ""),
            "scopus_id": x.get("dc:identifier", "")
        })
    return {"source": "Scopus", "count": len(records), "records": records}

@app.post("/api/search/wos")
async def search_wos(req: SearchRequest):
    if not WOS_API_KEY:
        raise HTTPException(503, "WOS_API_KEY is not configured.")
    params = {"databaseId": "WOS", "usrQuery": req.query, "count": req.limit, "firstRecord": 1}
    headers = {"X-ApiKey": WOS_API_KEY, "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=40) as client:
        try:
            r = await client.get("https://api.clarivate.com/api/wos", params=params, headers=headers)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Web of Science API request failed. Verify product entitlement and API version: {e}")
    payload = r.json()
    hits = payload.get("Data", {}).get("Records", {}).get("records", {}).get("REC", [])
    records = []
    for rec in hits:
        core = rec.get("static_data", {}).get("summary", {})
        title_data = core.get("titles", {}).get("title", [])
        title = next((x.get("content", "") for x in title_data if x.get("type") == "item"), "")
        pub = core.get("pub_info", {})
        records.append({"title": title, "authors": "", "year": pub.get("pubyear", ""),
                        "doi": "", "abstract": "", "language": "", "keywords": "",
                        "source": "", "url": ""})
    return {"source": "Web of Science", "count": len(records), "records": records,
            "note": "Provider payload fields vary by entitlement/API version; validate metadata mapping against your Clarivate response."}

@app.post("/api/ai/screen")
def ai_screen(req: ScreenRequest):
    client = openai_client()
    prompt = {
        "task": "Assess title and abstract against eligibility criteria for a systematic review.",
        "criteria": req.criteria,
        "records": [r.model_dump() for r in req.records],
        "instructions": [
            "Return JSON only with key results: array of objects {id, decision, confidence, rationale, evidence, missing_information}.",
            "decision must be include, exclude, or uncertain. Use uncertain if abstract is missing, ambiguous or insufficient.",
            "Never auto-exclude. Be conservative and recommend human verification.",
            "Cite only text present in supplied title, abstract or keywords. Do not invent facts, page numbers or full-text claims.",
            "Confidence is a number from 0 to 1, not a probability of truth.",
            "If criteria are incomplete, explain the uncertainty."
        ]
    }
    response = client.responses.create(model=AI_MODEL, input=json.dumps(prompt, ensure_ascii=False))
    return parse_json(output_text(response))

@app.post("/api/ai/extract")
def ai_extract(req: ExtractRequest):
    client = openai_client()
    prompt = {
        "task": "Create a cautious preliminary data-extraction draft from supplied bibliographic metadata and abstract.",
        "record": req.record,
        "schema": {"aim": "", "method": "", "context": "", "technology": "", "dataset": "",
                   "outcomes": "", "findings": "", "limitations": "", "gap": "", "evidence": ""},
        "instructions": [
            "Return JSON only. Use empty strings for unavailable information.",
            "Do not infer details absent from supplied text.",
            "The input is not full text; explicitly label uncertain or unreported items.",
            "Evidence locator must be empty unless a locator was provided in the input."
        ]
    }
    response = client.responses.create(model=AI_MODEL, input=json.dumps(prompt, ensure_ascii=False))
    return {"extraction": parse_json(output_text(response)), "source_scope": "metadata and abstract only; verify against full text"}

@app.post("/api/ai/synthesis")
def ai_synthesis(req: SynthesisRequest):
    client = openai_client()
    prompt = {
        "task": "Draft a structured, evidence-grounded narrative synthesis from supplied extracted studies.",
        "research_question": req.question, "included_records": req.records,
        "instructions": [
            "Do not add references, sample sizes, statistics, mechanisms or causal claims absent from supplied records.",
            "Distinguish consistent findings, contradictory findings, methodological limitations and evidence gaps.",
            "Mention study titles as traceability anchors. Identify where extraction is insufficient.",
            "Do not claim certainty or generalizability from study counts alone.",
            "Output sections: Overview; Themes; Agreement and disagreement; Methodological limitations; Research gaps; Claims requiring source verification."
        ]
    }
    response = client.responses.create(model=AI_MODEL, input=json.dumps(prompt, ensure_ascii=False))
    return {"text": output_text(response), "model": AI_MODEL, "advisory": True}
