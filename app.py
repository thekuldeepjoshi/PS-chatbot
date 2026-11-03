from contextlib import asynccontextmanager
import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from server import (
    CUSTOMERS,
    get_total_revenue,
    get_top_customers,
    search_customer,
    mcp,
)

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PS Chatbot | Business Analytics</title>
  <style>
    :root { color-scheme: dark; --bg:#0b1020; --panel:#121a2d; --line:#26334d; --muted:#9aa9c2; --accent:#7c9cff; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; background:radial-gradient(ellipse at top,#182646 0,#0b1020 55%); color:#eef3ff; font:16px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif; display:grid; place-items:center; padding:24px; }
    .shell { width:min(850px,100%); height:min(820px,calc(100vh - 48px)); min-height:540px; display:flex; flex-direction:column; background:rgba(18,26,45,.96); border:1px solid var(--line); border-radius:22px; overflow:hidden; box-shadow:0 24px 90px #0008; }
    header { padding:22px 26px; border-bottom:1px solid var(--line); display:flex; align-items:center; gap:14px; }
    .mark { width:42px;height:42px;border-radius:13px;background:linear-gradient(135deg,#7596ff,#8b67e8);display:grid;place-items:center;font-weight:800;color:white; }
    h1 { font-size:17px; margin:0; letter-spacing:.2px; } .sub { color:var(--muted);font-size:13px;margin-top:2px; }
    .status { margin-left:auto; color:#9fe3bd; font-size:12px; white-space:nowrap; } .dot { display:inline-block;width:7px;height:7px;background:#61d69a;border-radius:50%;margin-right:7px; }
    #messages { flex:1; overflow:auto; padding:26px; display:flex; flex-direction:column; gap:18px; }
    .msg { max-width:82%; padding:14px 17px; border:1px solid var(--line); border-radius:16px; white-space:pre-wrap; overflow-wrap:anywhere; }
    .bot { align-self:flex-start;background:#18243b;border-top-left-radius:5px; }
    .user { align-self:flex-end;background:#344b83;border-color:#4865a6;border-top-right-radius:5px; }
    .label { color:#a9bce8;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:5px; }
    .intro { color:#c2cde0; max-width:650px; } .suggestions { display:flex;flex-wrap:wrap;gap:9px;margin-top:14px; }
    .chip { background:#1c2942;color:#cbd8f3;border:1px solid #344665;border-radius:999px;padding:8px 12px;cursor:pointer;font-size:13px; }
    .chip:hover { border-color:var(--accent); }
    form { display:flex;gap:10px;padding:18px 22px;border-top:1px solid var(--line);background:#10182a; }
    input { flex:1;min-width:0;background:#0b1324;border:1px solid #34415b;border-radius:12px;padding:14px 15px;color:#fff;font:inherit;outline:none; }
    input:focus { border-color:var(--accent); } button.send { border:0;border-radius:12px;padding:0 20px;background:#718fff;color:#081126;font-weight:700;cursor:pointer; } button:disabled { opacity:.55;cursor:wait; }
    .note { padding:0 24px 15px;color:#7f8da7;font-size:11px;text-align:center; }
    @media(max-width:600px){body{padding:0}.shell{height:100vh;min-height:0;border-radius:0;border:0}header{padding:16px}.status{font-size:0}#messages{padding:18px}.msg{max-width:92%}form{padding:13px}.note{padding-bottom:10px}}
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div class="mark">PS</div>
      <div><h1>PS Business Assistant</h1><div class="sub">Customer and revenue analytics demo</div></div>
      <div class="status"><span class="dot"></span>Online</div>
    </header>
    <section id="messages" aria-live="polite">
      <div class="msg bot">
        <div class="label">Assistant</div>
        <div class="intro">Hi! I can help you explore the sample business data. Ask me about total revenue, top customers, or search for a customer.</div>
        <div class="suggestions">
          <button class="chip" data-q="What is the total revenue?">Total revenue</button>
          <button class="chip" data-q="Show me the top 3 customers">Top customers</button>
          <button class="chip" data-q="Search for Atlas">Search Atlas</button>
        </div>
      </div>
    </section>
    <form id="chat-form">
      <input id="message" autocomplete="off" placeholder="Ask about revenue or customers..." aria-label="Your message">
      <button class="send" id="send" type="submit">Send</button>
    </form>
    <div class="note">Demo uses fictional sample data. It does not connect to a live AI model.</div>
  </main>
<script>
  const messages = document.getElementById('messages');
  const input = document.getElementById('message');
  const form = document.getElementById('chat-form');
  const send = document.getElementById('send');

  function addMessage(text, who) {
    const bubble = document.createElement('div');
    bubble.className = 'msg ' + who;
    const label = document.createElement('div');
    label.className = 'label';
    label.textContent = who === 'user' ? 'You' : 'Assistant';
    const body = document.createElement('div');
    body.textContent = text;
    bubble.append(label, body);
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
  }

  async function ask(question) {
    if (!question.trim()) return;
    addMessage(question, 'user');
    input.value = '';
    send.disabled = true;
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({message: question})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Request failed');
      addMessage(data.reply, 'bot');
    } catch (error) {
      addMessage('I could not process that request. Please try again.', 'bot');
    } finally {
      send.disabled = false;
      input.focus();
    }
  }

  form.addEventListener('submit', event => {
    event.preventDefault();
    ask(input.value);
  });
  document.querySelectorAll('.chip').forEach(button => {
    button.addEventListener('click', () => ask(button.dataset.q));
  });
</script>
</body>
</html>
"""


class ChatRequest(BaseModel):
    message: str


@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield


# Keep the MCP endpoint available at /mcp alongside the browser chat UI.
mcp_app = mcp.streamable_http_app()
app = FastAPI(title="PS Business Assistant", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def home():
    return PAGE


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(payload: ChatRequest):
    message = payload.message.strip()
    if not message:
        return {"reply": "Please enter a question."}

    text = message.casefold()

    if any(word in text for word in ("help", "what can you do", "examples")):
        return {"reply": "Try asking: 'What is the total revenue?', 'Show the top 3 customers', or 'Search for Atlas'."}

    if "revenue" in text or "sales" in text or "turnover" in text or "total" in text:
        result = get_total_revenue()
        amount = result["total_revenue"]
        return {"reply": f"Total revenue across {len(CUSTOMERS)} customers is €{amount:,.2f}."}

    if any(word in text for word in ("top", "highest", "best", "largest")) and any(word in text for word in ("customer", "client", "account", "top")):
        match = re.search(r"\b(\d{1,2})\b", text)
        limit = min(int(match.group(1)), 20) if match else 3
        customers = get_top_customers(limit)
        lines = [f"{i}. {c['name']} · €{c['revenue']:,.2f}" for i, c in enumerate(customers, 1)]
        return {"reply": "Top customers by revenue:\n" + "\n".join(lines)}

    search_match = re.search(r"(?:search|find|look up)\s+(?:for\s+)?(.+)", message, re.IGNORECASE)
    if search_match:
        query = search_match.group(1).strip(" ?.!").strip()
        matches = search_customer(query) if query else []
        if not matches:
            return {"reply": f"I couldn't find a customer matching '{query}'."}
        lines = [f"{c['name']} · €{c['revenue']:,.2f} revenue · ID {c['id']}" for c in matches]
        return {"reply": "\n".join(lines)}

    return {"reply": "I can answer questions about total revenue, top customers, and customer lookup. Try: 'What is the total revenue?' or 'Show me the top 3 customers'."}


# Mount last so the app's own routes take precedence. The MCP endpoint remains /mcp.
app.mount("/", mcp_app)
