import json
import os

from mcp.server.fastmcp import FastMCP

# Render supplies PORT at runtime. Bind publicly so Render's proxy can reach us.
mcp = FastMCP(
    "business-analytics",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "10000")),
)

# Fictional demo data. All amounts are in EUR.
CUSTOMERS = [
    {"id": "C001", "name": "Northstar Labs", "revenue": 48200.0},
    {"id": "C002", "name": "Greenfield Foods", "revenue": 36750.0},
    {"id": "C003", "name": "Atlas Mobility", "revenue": 29100.0},
    {"id": "C004", "name": "Harbor Health", "revenue": 18400.0},
]


@mcp.tool()
def get_total_revenue() -> dict:
    """Return total revenue across all demo customers, in EUR."""
    total = sum(customer["revenue"] for customer in CUSTOMERS)
    return {"currency": "EUR", "total_revenue": round(total, 2)}


@mcp.tool()
def get_top_customers(limit: int = 3) -> list[dict]:
    """Return customers ranked by revenue, highest first."""
    if limit < 1 or limit > 20:
        raise ValueError("limit must be between 1 and 20")
    return sorted(CUSTOMERS, key=lambda customer: customer["revenue"], reverse=True)[:limit]


@mcp.tool()
def search_customer(name: str) -> list[dict]:
    """Find customers whose names contain the supplied text."""
    if not name.strip():
        raise ValueError("name cannot be empty")
    query = name.casefold()
    return [
        customer for customer in CUSTOMERS
        if query in customer["name"].casefold()
    ]


@mcp.tool()
def create_customer(customer_id: str, name: str, revenue: float = 0.0) -> dict:
    """Add a customer to the in-memory demo dataset."""
    if not customer_id.strip() or not name.strip():
        raise ValueError("customer_id and name are required")
    if revenue < 0:
        raise ValueError("revenue cannot be negative")
    if any(customer["id"] == customer_id for customer in CUSTOMERS):
        raise ValueError(f"customer id already exists: {customer_id}")

    customer = {
        "id": customer_id.strip(),
        "name": name.strip(),
        "revenue": round(float(revenue), 2),
    }
    CUSTOMERS.append(customer)
    return customer


@mcp.resource("business://customers")
def customer_directory() -> str:
    """Provide the current customer directory as JSON text."""
    return json.dumps(CUSTOMERS, indent=2)


@mcp.prompt()
def revenue_summary() -> str:
    """Create a prompt for summarizing the demo business revenue."""
    return (
        "Analyze the business customer data. Summarize total revenue, "
        "identify the top customer, and note any useful observations. "
        "State that the data is fictional demo data."
    )


if __name__ == "__main__":
    # Streamable HTTP is the network transport used by deployed MCP servers.
    mcp.run(transport="streamable-http")
