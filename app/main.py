import os, json
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import PlainTextResponse
from app.schemas import QueryRequest, SummarizeRequest, AssistantChatRequest, TaskCreate
from app.semantic import search_emails
from app.semantic import search_kb
from app.rag import build_summary_prompt, chat
from app.ingest import ingest_pull
from app.kb import ingest_pdf
from app.kb import ingest_zip
from app.insights import get_insights
from app.assistant import assistant_chat, extract_tasks_from_text, save_tasks

APP_TENANT_ID = os.getenv("APP_TENANT_ID")
GRAPH_CLIENT_STATE = os.getenv("GRAPH_CLIENT_STATE", "secretClientValue")

app = FastAPI(title="AI Email & Personal Assistant", default_response_class=None)

@app.get("/healthz")
def health():
    return {"ok": True}

# Webhook endpoint for Graph subscriptions (validation + notifications)
@app.post("/webhooks/graph", response_class=PlainTextResponse)
async def graph_webhook(request: Request):
    validation_token = request.query_params.get("validationToken")
    if validation_token:
        return PlainTextResponse(validation_token)
    body = await request.json()
    for notif in body.get("value", []):
        if notif.get("clientState") != GRAPH_CLIENT_STATE:
            raise HTTPException(status_code=401, detail="invalid client state")
        # TODO: enqueue notif.get("resourceData", {}).get("id") for ingestion
    return PlainTextResponse("OK")

@app.post("/ingest/pull")
def api_ingest_pull(user_upn: str):
    count = ingest_pull(user_upn, top=25)
    return {"ingested": count}

@app.post("/query")
def api_query(req: QueryRequest):
    hits = search_emails(req.question, k=req.k)
    messages = [{"role":"system","content":"Rispondi solo usando i PASSAGGI."},
                {"role":"user","content":"DOMANDA: " + req.question + "\n\nPASSAGGI:\n" + "\n\n---\n\n".join([h.get("snippet") or "" for h in hits])}]
    answer = chat(messages, temperature=0.1)
    return {"answer": answer, "references": [
        {"email_id": h.get("email_id"), "subject": h.get("subject"), "from": h.get("from_address"), "received_at": h.get("received_at")} for h in hits
    ]}

@app.post("/summarize")
def api_summarize(req: SummarizeRequest):
    # naive approach reusing semantic search to fetch recent/important items
    hits = search_emails("ultime email importanti", k=req.k)
    messages = build_summary_prompt(hits, instruction=req.instruction)
    summary = chat(messages, temperature=0.2)
    return {"summary": summary, "count": len(hits)}

@app.get("/insights")
def api_insights(k: int = 30):
    return get_insights(k=k)

# Upload a PDF to the knowledge base
@app.post("/kb/upload")
async def kb_upload(file: UploadFile = File(...), title: str = Form(None)):
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())
    doc_id = ingest_pdf(tmp_path, title=title or file.filename, source=file.filename)
    return {"ok": True, "doc_id": doc_id, "title": title or file.filename}

# General assistant chat (Email + KB)
@app.post("/assistant/chat")
def api_assistant_chat(req: AssistantChatRequest):
    return assistant_chat(req.message, req.upn, k_email=req.k_email, k_kb=req.k_kb)

# Extract tasks from free text or message and save
@app.post("/assistant/extract_tasks")
def api_extract_tasks(upn: str = Form(...), text: str = Form(...)):
    tasks = extract_tasks_from_text(text)
    saved = save_tasks(upn, tasks)
    return {"extracted": tasks, "saved": saved}

# Create a manual task quickly
@app.post("/assistant/task")
def api_task_create(req: TaskCreate):
    saved = save_tasks(req.upn, [{"title": req.title, "due_at": req.due_at, "priority": req.priority}])
    return {"saved": saved}

@app.post("/kb/upload-zip")
async def kb_upload_zip(file: UploadFile = File(...)):
    # Bulk upload: provide a .zip with pdf/txt/md/html/docx inside
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())
    count = ingest_zip(tmp_path)
    return {"ok": True, "ingested_files": count}

@app.get("/kb/search")
def kb_search(q: str, k: int = 8):
    hits = search_kb(q, k=k)
    return {"results": hits}
