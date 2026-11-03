import json
import os
from urllib.parse import quote

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "pharmapulse-intelligence",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "10000")),
)

# Private client/project examples remain fictional and separate from public evidence.
DRUGS = {
    "RX-214": {
        "drug_id": "RX-214",
        "drug_name": "RX-214 (fictional compound)",
        "client": "Northstar Therapeutics (fictional)",
        "therapeutic_area": "Oncology",
        "development_stage": "Preclinical",
        "testing_package": "Identity, purity, assay and stability testing",
    },
    "NX-508": {
        "drug_id": "NX-508",
        "drug_name": "NX-508 (fictional compound)",
        "client": "Harbor BioPharma (fictional)",
        "therapeutic_area": "Immunology",
        "development_stage": "Phase I support",
        "testing_package": "Analytical method validation and stability testing",
    },
}
PROJECTS = [
    {"project_id": "PRJ-1001", "client": "Northstar Therapeutics (fictional)", "drug": "RX-214", "status": "In progress", "next_milestone": "Stability timepoint review", "report_status": "Draft report in preparation"},
    {"project_id": "PRJ-1002", "client": "Harbor BioPharma (fictional)", "drug": "NX-508", "status": "Awaiting client review", "next_milestone": "Client comments on validation summary", "report_status": "Draft report shared"},
]
PUBLIC_SOURCES = {
    "PubChem": "https://pubchem.ncbi.nlm.nih.gov/",
    "ChEMBL": "https://www.ebi.ac.uk/chembl/",
    "DailyMed": "https://dailymed.nlm.nih.gov/",
    "openFDA": "https://open.fda.gov/apis/",
    "ClinicalTrials.gov": "https://clinicaltrials.gov/data-api",
    "FDA Drug Safety": "https://www.fda.gov/drugs/drug-safety-and-availability",
    "EMA News": "https://www.ema.europa.eu/en/news",
}


def get_drug_profile(drug_id: str) -> dict:
    result = DRUGS.get(drug_id.strip().upper())
    return result.copy() if result else {"error": f"No private demo drug record found for {drug_id}."}


def get_testing_status(drug_id: str) -> dict:
    drug = get_drug_profile(drug_id)
    if "error" in drug:
        return drug
    project = next((p for p in PROJECTS if p["drug"] == drug["drug_id"]), None)
    if not project:
        return {"error": f"No demo testing project found for {drug_id}."}
    return {"drug_id": drug["drug_id"], "drug_name": drug["drug_name"], "stage": drug["development_stage"],
            "status": project["status"], "updated": "2026-10-28 (sample date)",
            "next_milestone": project["next_milestone"], "report_status": project["report_status"]}


def get_client_projects() -> list[dict]:
    return [p.copy() for p in PROJECTS]


async def _get_json(client: httpx.AsyncClient, url: str, params: dict | None = None) -> dict:
    response = await client.get(url, params=params)
    response.raise_for_status()
    return response.json()


async def search_public_drug(query: str) -> dict:
    """Search public compound/drug references. Public records are not client test results."""
    term = query.strip()
    if not term:
        return {"error": "Enter a drug or compound name."}
    timeout = httpx.Timeout(15.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": "PharmaClientIntelligenceDemo/1.0"}) as client:
        pubchem_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(term, safe='')}/property/MolecularFormula,MolecularWeight,IUPACName/JSON"
        chembl_url = "https://www.ebi.ac.uk/chembl/api/data/molecule/search.json"
        fda_url = "https://api.fda.gov/drug/label.json"
        results = await __import__("asyncio").gather(
            _get_json(client, pubchem_url),
            _get_json(client, chembl_url, {"q": term, "limit": 3}),
            _get_json(client, fda_url, {"search": f'openfda.generic_name:"{term}" OR openfda.brand_name:"{term}"', "limit": 2}),
            return_exceptions=True,
        )

    output = {"query": term, "sources": [], "pubchem": None, "chembl": [], "fda_labels": []}
    pubchem, chembl, fda = results
    if not isinstance(pubchem, Exception):
        props = pubchem.get("PropertyTable", {}).get("Properties", [])
        if props:
            p = props[0]
            output["pubchem"] = {k: p.get(k) for k in ("CID", "MolecularFormula", "MolecularWeight", "IUPACName")}
            output["sources"].append({"name": "PubChem", "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{p.get('CID')}"})
    if not isinstance(chembl, Exception):
        for m in chembl.get("molecules", [])[:3]:
            output["chembl"].append({k: m.get(k) for k in ("molecule_chembl_id", "pref_name", "max_phase", "molecule_type")})
        if output["chembl"]:
            output["sources"].append({"name": "ChEMBL", "url": "https://www.ebi.ac.uk/chembl/"})
    if not isinstance(fda, Exception):
        for label in fda.get("results", [])[:2]:
            openfda = label.get("openfda", {})
            output["fda_labels"].append({
                "brand_name": (openfda.get("brand_name") or [])[:2],
                "generic_name": (openfda.get("generic_name") or [])[:2],
                "manufacturer": (openfda.get("manufacturer_name") or [])[:2],
                "effective_time": label.get("effective_time"),
                "indications": (label.get("indications_and_usage") or [""])[0][:1200],
                "warnings": (label.get("warnings") or label.get("warnings_and_cautions") or [""])[0][:1200],
            })
        if output["fda_labels"]:
            output["sources"].append({"name": "openFDA drug labeling", "url": "https://open.fda.gov/apis/drug/label/"})
    if not any((output["pubchem"], output["chembl"], output["fda_labels"])):
        output["message"] = "No matching public record was returned by PubChem, ChEMBL or openFDA. Try a generic name, brand name or synonym."
    output["retrieved_from"] = "Live public APIs"
    return output


async def search_clinical_trials(query: str, page_size: int = 5) -> dict:
    """Search registered clinical studies by intervention or drug name."""
    term = query.strip()
    if not term:
        return {"error": "Enter a drug, intervention or condition to search."}
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
        data = await _get_json(client, "https://clinicaltrials.gov/api/v2/studies",
                               {"query.intr": term, "pageSize": max(1, min(page_size, 10)), "format": "json"})
    studies = []
    for item in data.get("studies", []):
        p = item.get("protocolSection", {})
        ident = p.get("identificationModule", {})
        status = p.get("statusModule", {})
        design = p.get("designModule", {})
        studies.append({
            "nct_id": ident.get("nctId"),
            "title": ident.get("briefTitle"),
            "status": status.get("overallStatus"),
            "phase": design.get("phases", []),
            "start_date": (status.get("startDateStruct") or {}).get("date"),
            "url": "https://clinicaltrials.gov/study/" + str(ident.get("nctId", "")),
        })
    return {"query": term, "count_returned": len(studies), "studies": studies,
            "source": "ClinicalTrials.gov API v2", "source_url": "https://clinicaltrials.gov/data-api"}


async def search_fda_safety(query: str = "") -> dict:
    """Retrieve recent public FDA drug enforcement/recall records, optionally filtered by product."""
    params = {"limit": 5, "sort": "report_date:desc"}
    if query.strip():
        params["search"] = f'product_description:"{query.strip()}"'
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
        data = await _get_json(client, "https://api.fda.gov/drug/enforcement.json", params)
    records = []
    for r in data.get("results", []):
        records.append({k: r.get(k) for k in ("recall_number", "status", "classification", "product_description", "reason_for_recall", "report_date", "recalling_firm", "recall_url")})
    return {"records": records, "source": "openFDA drug enforcement API", "source_url": "https://open.fda.gov/apis/drug/enforcement/"}


async def smart_answer(question: str) -> str:
    """Intent-route a browser chat question to private demo records or live public datasets."""
    import re

    q = question.casefold().strip()
    if not q:
        return "Please enter a question."

    def subject() -> str:
        match = re.search(r"\\b(?:for|about|of|on)\\s+([A-Za-z0-9][A-Za-z0-9 .-]{1,55})", question, re.I)
        if match:
            value = match.group(1).strip(" .?!")
            return re.split(r"\\b(?:and|with|including|in|status|profile|information)\\b", value, flags=re.I)[0].strip()
        code = re.search(r"\\b[A-Z]{2,5}-?\\d{2,5}\\b", question, re.I)
        return code.group(0) if code else ""

    if any(x in q for x in ("my project", "client project", "project status", "project milestone", "report status", "my testing", "our project")):
        lines = ["Private project workspace (fictional demo records):"]
        lines.extend(f"- {p['project_id']} | {p['client']} | {p['drug']} | {p['status']} | Next: {p['next_milestone']} | Report: {p['report_status']}" for p in get_client_projects())
        lines.append("These are sample records, not live client data.")
        return "\\n".join(lines)

    code = re.search(r"\\b[A-Z]{2,5}-?\\d{2,5}\\b", question, re.I)
    if any(x in q for x in ("testing status", "test status", "testing progress", "milestone", "report availability")):
        if code and code.group(0).upper() in DRUGS:
            r = get_testing_status(code.group(0))
            return f"Fictional demo testing record for {r['drug_id']}:\\nStage: {r['stage']}\\nStatus: {r['status']}\\nLast updated: {r['updated']}\\nNext milestone: {r['next_milestone']}\\nReport: {r['report_status']}\\nThis is not a live laboratory result."
        return "I can show fictional sample project records only. Which sample compound ID do you want to check? Public databases do not contain your company's laboratory testing status."

    if any(x in q for x in ("clinical trial", "clinical study", "trial search", "study search", "trials for", "studies for")):
        term = subject()
        if not term:
            return "Which drug, intervention or condition should I search on ClinicalTrials.gov?"
        try:
            data = await search_clinical_trials(term)
            lines = [f"ClinicalTrials.gov results for: {term}"]
            for s in data.get("studies", []):
                lines.append(f"- {s.get('nct_id')}: {s.get('title')} | Status: {s.get('status')} | Phase: {', '.join(s.get('phase') or []) or 'Not specified'} | {s.get('url')}")
            if not data.get("studies"):
                lines.append("No matching studies were returned.")
            lines.append("Source: " + data["source_url"] + ". Check the registry record for the latest sponsor-submitted information.")
            return "\\n".join(lines)
        except Exception:
            return "ClinicalTrials.gov could not be reached right now. Try https://clinicaltrials.gov/ directly."

    if any(x in q for x in ("recall", "drug safety", "safety alert", "enforcement", "withdrawn")):
        term = subject()
        try:
            data = await search_fda_safety(term)
            lines = ["Recent FDA drug enforcement/recall records:"]
            for r in data.get("records", []):
                lines.append(f"- {r.get('product_description') or 'Product not stated'} | {r.get('status')} | Class {r.get('classification')} | Date: {r.get('report_date')} | Reason: {r.get('reason_for_recall')}")
            if not data.get("records"):
                lines.append("No matching records were returned.")
            lines.append("Source: " + data["source_url"])
            lines.append("This is recall/enforcement data, not a complete adverse-event database or clinical risk assessment.")
            return "\\n".join(lines)
        except Exception:
            return "openFDA could not be reached. Try https://www.fda.gov/drugs/drug-safety-and-availability."

    if any(x in q for x in ("drug", "compound", "medicine", "medication", "molecule", "pubchem", "chembl", "drug profile")):
        term = subject()
        if not term and code and code.group(0).upper() in DRUGS:
            d = get_drug_profile(code.group(0))
            return f"Private demo drug profile: {d['drug_id']} | {d['drug_name']}\\nClient: {d['client']}\\nTherapeutic area: {d['therapeutic_area']}\\nStage: {d['development_stage']}\\nTesting package: {d['testing_package']}\\nFictional sample record, separate from public datasets."
        if not term:
            return "Which drug or compound should I look up? Provide a generic name, brand name, synonym or ChEMBL ID."
        try:
            data = await search_public_drug(term)
            lines = [f"Public drug/compound lookup: {term}"]
            if data.get("pubchem"):
                lines.append("PubChem: " + json.dumps(data["pubchem"], ensure_ascii=False))
            if data.get("chembl"):
                lines.append("ChEMBL: " + json.dumps(data["chembl"], ensure_ascii=False))
            for label in data.get("fda_labels", []):
                lines.append("FDA label: " + json.dumps(label, ensure_ascii=False))
            if data.get("message"):
                lines.append(data["message"])
            lines.extend("Source: " + s["name"] + " " + s["url"] for s in data.get("sources", []))
            lines.append("Retrieved live from public APIs. These records are reference information, not laboratory results, clinical advice or proof of approval in every jurisdiction.")
            return "\\n".join(lines)
        except Exception:
            return "Public drug databases could not be reached just now. Try PubChem, ChEMBL or openFDA directly."

    if any(x in q for x in ("news", "fda", "ema", "regulatory update", "pharma update", "data sources", "open data")):
        return "\\n".join(f"{name}: {url}" for name, url in PUBLIC_SOURCES.items())

    return "I can search public drug references (PubChem, ChEMBL, openFDA), clinical studies (ClinicalTrials.gov), and FDA recall records. I can also show fictional project examples. Try 'drug profile for aspirin', 'clinical trials for pembrolizumab', or 'show my project milestones'."


@mcp.tool()
def drug_profile(drug_id: str) -> dict:
    """Get a fictional private demo drug profile by identifier."""
    return get_drug_profile(drug_id)


@mcp.tool()
def testing_status(drug_id: str) -> dict:
    """Get fictional sample testing stage, status, report status and next milestone."""
    return get_testing_status(drug_id)


@mcp.tool()
def client_projects() -> list[dict]:
    """List fictional sample client projects and milestones."""
    return get_client_projects()


@mcp.tool()
async def public_drug_lookup(query: str) -> dict:
    """Look up a drug/compound in public PubChem, ChEMBL and openFDA sources."""
    return await search_public_drug(query)


@mcp.tool()
async def clinical_trial_search(query: str, page_size: int = 5) -> dict:
    """Search ClinicalTrials.gov for registered studies by intervention/drug."""
    return await search_clinical_trials(query, page_size)


@mcp.tool()
async def fda_drug_safety_search(query: str = "") -> dict:
    """Search recent public FDA drug recall/enforcement records."""
    return await search_fda_safety(query)


@mcp.tool()
def public_data_sources() -> dict:
    """List the public pharmaceutical data sources used by this assistant."""
    return PUBLIC_SOURCES.copy()


@mcp.resource("pharma://demo/drugs")
def drug_directory() -> str:
    return json.dumps(list(DRUGS.values()), indent=2)


@mcp.resource("pharma://demo/projects")
def project_directory() -> str:
    return json.dumps(PROJECTS, indent=2)


@mcp.prompt()
def client_project_brief() -> str:
    return ("Prepare a concise client project status brief using only approved private project records. "
            "Separate confirmed results from pending work, include report status and next milestones, "
            "and never infer clinical conclusions from public databases.")
