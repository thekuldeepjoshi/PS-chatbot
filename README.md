# Pharma Client Intelligence

A browser-based demo and MCP server concept for a pharmaceutical testing services business. It helps client users explore drug profiles, sample testing status, project milestones and trusted public pharmaceutical information sources.

## Features

- Browser chat interface for drug, testing and project questions.
- MCP tools for drug profiles, testing status, project lists and pharma news sources.
- MCP resources for demo drug and project directories.
- Links to FDA, EMA and ClinicalTrials.gov public information.
- Render deployment using FastAPI and Streamable HTTP MCP.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://localhost:8000`. MCP endpoint: `http://localhost:8000/mcp`.

## Render

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Root directory: blank
- Branch: `main`

## Example questions

- Show drug RX-214.
- What is the testing status?
- Show my project milestones.
- Show latest pharma news sources.

## Important limitations

All drug, client, project, status and milestone records in this repository are fictional examples. The news section links to public sources; it does not currently retrieve, rank or summarize live news. This prototype is not a validated laboratory information system, regulatory system or clinical decision support tool.

Before using it with real clients, implement verified client authentication and authorization, tenant-level data isolation, secure document storage, audit trails, retention policies, and review of regulatory and scientific content. Do not put patient-identifiable data, confidential client records or unpublished trial data into this public demo.

## Official public information

- [FDA Drug Safety and Availability](https://www.fda.gov/drugs/drug-safety-and-availability)
- [European Medicines Agency News](https://www.ema.europa.eu/en/news)
- [ClinicalTrials.gov](https://clinicaltrials.gov/)
- [MCP documentation](https://modelcontextprotocol.io/)
