import json
import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "pharma-client-intelligence",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "10000")),
)

# Entirely fictional demonstration records. Never use these as clinical evidence.
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
    {
        "project_id": "PRJ-1001",
        "client": "Northstar Therapeutics (fictional)",
        "drug": "RX-214",
        "status": "In progress",
        "next_milestone": "Stability timepoint review",
        "report_status": "Draft report in preparation",
    },
    {
        "project_id": "PRJ-1002",
        "client": "Harbor BioPharma (fictional)",
        "drug": "NX-508",
        "status": "Awaiting client review",
        "next_milestone": "Client comments on validation summary",
        "report_status": "Draft report shared",
    },
]

NEWS_SOURCES = [
    {"name": "FDA Drug Safety and Availability", "url": "https://www.fda.gov/drugs/drug-safety-and-availability"},
    {"name": "European Medicines Agency News", "url": "https://www.ema.europa.eu/en/news"},
    {"name": "ClinicalTrials.gov", "url": "https://clinicaltrials.gov/"},
    {"name": "FDA Drug Development and Approval", "url": "https://www.fda.gov/drugs/development-approval-process-drugs"},
]


def get_drug_profile(drug_id: str) -> dict:
    """Look up a fictional demo drug profile by its identifier."""
    result = DRUGS.get(drug_id.strip().upper())
    return result.copy() if result else {"error": f"No demo drug found for {drug_id}."}


def get_testing_status(drug_id: str) -> dict:
    """Return fictional testing status and next milestone for a demo drug."""
    drug = get_drug_profile(drug_id)
    if "error" in drug:
        return drug
    project = next((p for p in PROJECTS if p["drug"] == drug["drug_id"]), None)
    if not project:
        return {"error": f"No demo testing project found for {drug_id}."}
    return {
        "drug_id": drug["drug_id"],
        "drug_name": drug["drug_name"],
        "stage": drug["development_stage"],
        "status": project["status"],
        "updated": "2026-10-28 (sample date)",
        "next_milestone": project["next_milestone"],
    }


def get_client_projects() -> list[dict]:
    """Return the fictional sample client project list."""
    return [project.copy() for project in PROJECTS]


def get_pharma_news_sources() -> list[dict]:
    """Return trusted public sources where users can check current pharma news."""
    return [source.copy() for source in NEWS_SOURCES]


@mcp.tool()
def drug_profile(drug_id: str) -> dict:
    """Get a fictional demo drug profile by drug identifier."""
    return get_drug_profile(drug_id)


@mcp.tool()
def testing_status(drug_id: str) -> dict:
    """Get fictional testing stage, status and next milestone for a demo drug."""
    return get_testing_status(drug_id)


@mcp.tool()
def client_projects() -> list[dict]:
    """List fictional client projects and their next milestones."""
    return get_client_projects()


@mcp.tool()
def pharma_news_sources() -> list[dict]:
    """List trusted public sources for current pharma and regulatory news."""
    return get_pharma_news_sources()


@mcp.resource("pharma://demo/drugs")
def drug_directory() -> str:
    """Read the fictional demo drug directory as JSON."""
    return json.dumps(list(DRUGS.values()), indent=2)


@mcp.resource("pharma://demo/projects")
def project_directory() -> str:
    """Read fictional client project milestones as JSON."""
    return json.dumps(PROJECTS, indent=2)


@mcp.prompt()
def client_project_brief() -> str:
    """Prompt template for preparing a client project status brief."""
    return (
        "Prepare a concise client project status brief using only approved "
        "project records. Separate confirmed results from pending work, "
        "include report status and next milestones, and flag missing data. "
        "Do not infer clinical conclusions."
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
