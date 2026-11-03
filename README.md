# PS Chatbot: Browser Chat + MCP Server

A small business analytics chatbot with a browser interface and an MCP server. It uses fictional customer data for demonstration.

## Browser app

Open the deployed Render URL to use the chat interface. Try:
- "What is the total revenue?"
- "Show me the top 3 customers"
- "Search for Atlas"

The browser chat is a deterministic demo, not a connection to an external AI model. It supports the sample analytics intents without requiring an API key.

## MCP endpoint

The MCP Streamable HTTP endpoint is available at `/mcp` on the same host.

## Deploy on Render

The repository includes a Render Blueprint. Create a Blueprint from this repository, or configure a Web Service with:
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Branch: `main`

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://localhost:8000` for the chat UI. The MCP endpoint is `http://localhost:8000/mcp`.

## MCP capabilities

Tools:
- `get_total_revenue()`
- `get_top_customers(limit)`
- `search_customer(name)`
- `create_customer(customer_id, name, revenue)`

Resource: `business://customers`

Prompt: `revenue_summary`

The data is fictional and held in memory, so changes reset when the service restarts. For production, add persistent storage, authentication, authorization, and robust monitoring.

## References

- [MCP Python SDK: ASGI deployment](https://py.sdk.modelcontextprotocol.io/run/asgi/)
- [Render Web Services](https://render.com/docs/web-services)
