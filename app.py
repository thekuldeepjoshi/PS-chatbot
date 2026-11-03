from contextlib import asynccontextmanager
import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from server import (
    DRUGS,
    PROJECTS,
    get_drug_profile,
    get_testing_status,
    get_client_projects,
    smart_answer,
    mcp,
)

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pharma Client Intelligence</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#121e31;--line:#293a52;--muted:#9eb0c8;--accent:#6da8ff;--green:#76d6b0}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(145deg,#0c1728,#0a1020 65%);color:#edf4ff;font:15px/1.5 Inter,system-ui,sans-serif}
.wrap{max-width:1120px;margin:auto;padding:28px 22px 50px}.top{display:flex;align-items:center;gap:14px;margin-bottom:28px}.logo{width:46px;height:46px;border-radius:14px;background:linear-gradient(135deg,#448ee8,#4cc5b0);display:grid;place-items:center;font-weight:800;font-size:18px}.top h1{margin:0;font-size:22px}.top p{margin:3px 0 0;color:var(--muted);font-size:13px}.pill{margin-left:auto;border:1px solid #315b52;color:#9ce3c7;border-radius:30px;padding:6px 11px;font-size:12px}
.hero{padding:28px;border:1px solid var(--line);border-radius:20px;background:linear-gradient(120deg,#172b45,#142339);margin-bottom:20px}.eyebrow{color:#8dbdff;text-transform:uppercase;letter-spacing:1.6px;font-size:11px;font-weight:700}.hero h2{font-size:28px;line-height:1.2;margin:9px 0}.hero p{max-width:720px;color:#b8c8dd;margin:0}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:16px 0 24px}.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:19px}.card h3{margin:0 0 7px;font-size:16px}.card p{margin:0;color:var(--muted);font-size:13px}.card .symbol{font-size:22px;margin-bottom:10px}.section{font-size:17px;margin:24px 0 12px}.workspace{display:grid;grid-template-columns:1.4fr .8fr;gap:16px}.chat,.side{background:var(--panel);border:1px solid var(--line);border-radius:17px;overflow:hidden}.head{padding:15px 18px;border-bottom:1px solid var(--line);font-weight:650}.chatlog{height:330px;overflow:auto;padding:18px;display:flex;flex-direction:column;gap:12px}.bubble{max-width:88%;padding:12px 14px;border-radius:13px;white-space:pre-wrap}.bot{background:#1b2b43;align-self:flex-start}.user{background:#28528a;align-self:flex-end}.small{font-size:11px;color:#9fb6d4;margin-bottom:4px}.compose{display:flex;gap:9px;padding:13px;border-top:1px solid var(--line)}input{flex:1;min-width:0;background:#0b1525;border:1px solid #354961;border-radius:10px;color:white;padding:12px;font:inherit}button{cursor:pointer}button.send{background:#78a9ff;border:0;border-radius:10px;padding:0 17px;color:#08172b;font-weight:700}.quick{display:flex;flex-wrap:wrap;gap:8px;padding:0 16px 15px}.quick button{border:1px solid #3a526d;background:#1a2b43;color:#c8dcf4;border-radius:30px;padding:7px 10px;font-size:12px}.side .item{padding:14px 17px;border-bottom:1px solid var(--line)}.item:last-child{border:0}.item strong{display:block;font-size:13px}.item span{display:block;color:var(--muted);font-size:12px;margin-top:4px}.item a{color:#91baff;text-decoration:none;font-size:12px}.notice{margin-top:18px;padding:12px 14px;background:#2a2618;border:1px solid #64522c;color:#e9d8a9;border-radius:12px;font-size:12px}.footer{text-align:center;color:#71849e;font-size:11px;margin-top:18px}
@media(max-width:800px){.grid{grid-template-columns:1fr}.workspace{grid-template-columns:1fr}.hero h2{font-size:23px}}@media(max-width:500px){.wrap{padding:18px 12px}.pill{font-size:0}.chatlog{height:300px}}
</style>
</head>
<body><main class="wrap">
<header class="top"><div class="logo">PI</div><div><h1>Pharma Client Intelligence</h1><p>Drug testing, project visibility and industry updates</p></div><div class="pill">DEMO ENVIRONMENT</div></header>
<section class="hero"><div class="eyebrow">Client portal assistant</div><h2>Your testing projects, in one place.</h2><p>Ask about drug profiles, testing milestones, project progress and trusted pharmaceutical news sources. This preview uses fictional sample records.</p></section>
<section class="grid">
<div class="card"><div class="symbol">🧪</div><h3>Drug information</h3><p>View sample compound profiles, test stages, methods and milestone status.</p></div>
<div class="card"><div class="symbol">📋</div><h3>Client projects</h3><p>Check project progress, next milestones and report availability.</p></div>
<div class="card"><div class="symbol">🌐</div><h3>Pharma news</h3><p>Open official FDA, EMA and clinical-trial information sources.</p></div>
</section>
<h2 class="section">Ask the assistant</h2>
<section class="workspace">
<div class="chat"><div class="head">Pharma support assistant</div><div class="chatlog" id="log" aria-live="polite"><div class="bubble bot"><div class="small">ASSISTANT</div>Hello. Ask me about a sample drug, testing status, your project milestones, or pharmaceutical news sources.</div></div>
<div class="quick"><button data-q="Show drug RX-214">Drug profile</button><button data-q="What is the testing status?">Testing status</button><button data-q="Show my project milestones">Project milestones</button><button data-q="Show latest pharma news sources">Pharma news</button></div>
<form class="compose" id="form"><input id="question" placeholder="Ask about a drug, project or pharma news..." autocomplete="off"><button class="send">Send</button></form></div>
<aside class="side"><div class="head">Trusted information sources</div>
<div class="item"><strong>FDA Drug Safety & Availability</strong><span>US safety communications and drug updates</span><a href="https://www.fda.gov/drugs/drug-safety-and-availability" target="_blank" rel="noopener">Open FDA source ↗</a></div>
<div class="item"><strong>EMA News</strong><span>European medicines and regulatory updates</span><a href="https://www.ema.europa.eu/en/news" target="_blank" rel="noopener">Open EMA news ↗</a></div>
<div class="item"><strong>ClinicalTrials.gov</strong><span>Registered clinical studies and results</span><a href="https://clinicaltrials.gov/" target="_blank" rel="noopener">Search clinical trials ↗</a></div>
<div class="item"><strong>FDA Drug Approvals</strong><span>New drug approvals and review information</span><a href="https://www.fda.gov/drugs/development-approval-process-drugs" target="_blank" rel="noopener">Open FDA approvals ↗</a></div>
</aside></section>
<div class="notice"><strong>Confidentiality and safety:</strong> This is a demonstration using fictional drug and client records. Do not enter real client confidential information, patient data or unpublished trial results. Production access controls, verified data sources and audit logging are required before client use.</div>
<div class="footer">Pharma Client Intelligence · Prototype · Not for clinical decision-making</div>
</main>
<script>
const log=document.getElementById('log'),form=document.getElementById('form'),input=document.getElementById('question');
function add(text,who){const b=document.createElement('div');b.className='bubble '+who;const label=document.createElement('div');label.className='small';label.textContent=who==='user'?'YOU':'ASSISTANT';const body=document.createElement('div');body.textContent=text;b.append(label,body);log.append(b);log.scrollTop=log.scrollHeight}
async function ask(q){q=q.trim();if(!q)return;add(q,'user');input.value='';try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:q})});const d=await r.json();add(d.reply||'No response available.','bot')}catch(e){add('Unable to reach the assistant. Please try again.','bot')}}
form.addEventListener('submit',e=>{e.preventDefault();ask(input.value)});document.querySelectorAll('.quick button').forEach(b=>b.addEventListener('click',()=>ask(b.dataset.q)));
</script></body></html>"""


class ChatRequest(BaseModel):
    message: str


@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="PharmaPulse Intelligence", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def home():
    return PAGE


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(payload: ChatRequest):
    return {"reply": await smart_answer(payload.message)}


# MCP tools remain available on the same service at /mcp.
app.mount("/mcp", mcp.streamable_http_app())
