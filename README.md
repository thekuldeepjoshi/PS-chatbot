# PharmaPulse Intelligence

A browser-based pharmaceutical information assistant and MCP server prototype. It separates live public scientific/regulatory reference data from fictional private client-project examples.

## Live public data integrations

- **PubChem PUG REST:** compound identifiers, molecular formula, molecular weight and IUPAC name.
- **ChEMBL API:** public molecule records and development-phase metadata where available.
- **openFDA drug labeling:** public product labels, indications and warning text.
- **ClinicalTrials.gov API v2:** registered study titles, NCT identifiers, recruitment status, phase and start date.
- **openFDA drug enforcement:** public drug recall and enforcement records.

The browser assistant routes questions to these sources and includes source links in responses. Public API results are retrieved at query time and can be unavailable or incomplete. The prototype does not currently provide a live FDA/EMA news feed.

## Private demo data

The sample drug profiles, client names, project statuses, milestones and report statuses are fictional. They are kept separate from public database results. Public datasets cannot provide your company's laboratory results, testing status or confidential client information.

## Example questions

- drug profile for aspirin
- look up metformin
- clinical trials for pembrolizumab
- recent FDA recalls for valsartan
- show my project milestones
- testing status for RX-214

## Run locally

    python -m venv .venv
    source .venv/bin/activate
    # Windows: .venv\\Scripts\\activate
    pip install -r requirements.txt
    uvicorn app:app --reload

Open http://localhost:8000. MCP endpoint: http://localhost:8000/mcp.

## Render

- Build command: pip install -r requirements.txt
- Start command: uvicorn app:app --host 0.0.0.0 --port $PORT
- Root directory: blank
- Branch: main

## Public API references

- [PubChem PUG REST](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest)
- [ChEMBL web services](https://chembl.gitbook.io/chembl-interface-documentation/web-services)
- [openFDA APIs](https://open.fda.gov/apis/)
- [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/about-api)

## Important limitations and safety

This is a prototype, not a validated laboratory information management system (LIMS), regulatory system or clinical decision-support tool. Public database entries are reference information, not laboratory test results, medical advice or proof of approval in every jurisdiction. Registry data may be sponsor-submitted and may change. Recall/enforcement records are not a complete adverse-event database.

Before real client use, implement verified authentication and authorization, tenant-level data isolation, secure document storage, audit trails, retention policies, rate limiting, monitoring, and scientific/regulatory review. Do not enter patient-identifiable data, confidential client records or unpublished trial results into this public demo.