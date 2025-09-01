import os, json
from typing import Dict, Any, List
from app.semantic import search_emails, search_kb
from app.rag import build_qa_prompt, chat
from app.db import get_client

APP_TENANT_ID = os.getenv("APP_TENANT_ID")

def assistant_chat(message: str, upn: str | None, k_email:int=6, k_kb:int=6) -> Dict[str, Any]:
    email_hits = search_emails(message, k=k_email)
    kb_hits = search_kb(message, k=k_kb)
    # Merge passages
    passages = []
    for h in email_hits:
        passages.append({"from_address": h.get("from_address"), "received_at": h.get("received_at"),
                         "subject": h.get("subject"), "snippet": h.get("snippet"), "body_text": h.get("body_text")})
    for kb in kb_hits:
        passages.append({"from_address": "KB", "received_at": "", "subject": kb.get("title"),
                         "snippet": kb.get("content"), "body_text": kb.get("content")})
    msgs = build_qa_prompt(message, passages)
    answer = chat(msgs, temperature=0.2)
    return {"answer": answer, "email_refs": email_hits, "kb_refs": kb_hits}

def extract_tasks_from_text(text: str) -> List[Dict[str, Any]]:
    messages = [
        {"role":"system","content":"Estrai TODO come JSON array con oggetti: {title, due_at (ISO opzionale), priority in [low,medium,high]}"},
        {"role":"user","content": text}
    ]
    raw = chat(messages, temperature=0)
    try:
        return json.loads(raw)
    except Exception:
        return []

def save_tasks(upn: str, tasks: List[Dict[str, Any]]):
    supa = get_client()
    out = []
    for t in tasks:
        rec = supa.table("tasks").insert({
            "tenant_id": APP_TENANT_ID,
            "upn": upn,
            "title": t.get("title"),
            "due_at": t.get("due_at"),
            "priority": (t.get("priority") or "medium")
        }).execute().data[0]
        out.append(rec)
    return out
