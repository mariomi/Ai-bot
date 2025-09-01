import os
from typing import Dict, Any, List
from app.db import get_client
from app.graph import list_messages, get_message
from app.utils import html_to_text
from app.rag import embed

APP_TENANT_ID = os.getenv("APP_TENANT_ID")

def _ensure_mailbox(supa, tenant_id, upn: str) -> str:
    r = supa.table("mailboxes").select("*").eq("tenant_id", tenant_id).eq("user_principal_name", upn).limit(1).execute()
    if r.data:
        return r.data[0]["id"]
    ins = supa.table("mailboxes").insert({"tenant_id": tenant_id, "user_principal_name": upn}).execute()
    return ins.data[0]["id"]

def _ensure_thread(supa, tenant_id, mailbox_id, m):
    thread_key = m.get("conversationId")
    subject = m.get("subject")
    r = supa.table("threads").select("*").eq("tenant_id", tenant_id).eq("mailbox_id", mailbox_id).eq("thread_key", thread_key).limit(1).execute()
    if r.data:
        return r.data[0]["id"]
    ins = supa.table("threads").insert({
        "tenant_id": tenant_id,
        "mailbox_id": mailbox_id,
        "thread_key": thread_key,
        "subject": subject,
        "first_message_at": m.get("sentDateTime"),
        "last_message_at": m.get("receivedDateTime"),
        "participants": {}
    }).execute()
    return ins.data[0]["id"]

def normalize_graph_message(full: dict) -> dict:
    def addr(x):
        if not x: return None
        return x["emailAddress"]["address"]
    def addr_list(xs):
        if not xs: return []
        return [a["emailAddress"]["address"] for a in xs]
    headers = {h["name"].lower(): h["value"] for h in full.get("internetMessageHeaders", [])} if full.get("internetMessageHeaders") else {}
    return {
        "provider_message_id": full["id"],
        "from_address": addr(full.get("from")),
        "to_addresses": addr_list(full.get("toRecipients")),
        "cc_addresses": addr_list(full.get("ccRecipients")),
        "bcc_addresses": addr_list(full.get("bccRecipients")),
        "sent_at": full.get("sentDateTime"),
        "received_at": full.get("receivedDateTime"),
        "subject": full.get("subject"),
        "body_html": full.get("body", {}).get("content"),
        "importance": full.get("importance", "normal"),
        "labels": [],
        "has_attachments": full.get("hasAttachments", False),
        "in_reply_to": headers.get("in-reply-to")
    }

def upsert_email_with_embeddings(supa, tenant_id: str, mailbox_id: str, thread_id: str, email: dict) -> str:
    body_text = email.get("body_text") or html_to_text(email.get("body_html"))
    ins = supa.table("emails").insert({
        "tenant_id": tenant_id,
        "mailbox_id": mailbox_id,
        "thread_id": thread_id,
        "provider_message_id": email["provider_message_id"],
        "from_address": email.get("from_address"),
        "to_addresses": email.get("to_addresses"),
        "cc_addresses": email.get("cc_addresses"),
        "bcc_addresses": email.get("bcc_addresses"),
        "sent_at": email.get("sent_at"),
        "received_at": email.get("received_at"),
        "subject": email.get("subject"),
        "body_text": body_text,
        "body_html": email.get("body_html"),
        "importance": email.get("importance","normal"),
        "labels": email.get("labels", []),
        "has_attachments": email.get("has_attachments", False),
        "in_reply_to": email.get("in_reply_to")
    }).execute()
    email_id = ins.data[0]["id"]
    # Simple chunking
    chunks = [body_text[i:i+6000] for i in range(0, len(body_text), 6000)] or [""]
    for idx, ch in enumerate(chunks):
        vec = embed(ch)
        supa.table("email_embeddings").insert({
            "email_id": email_id,
            "tenant_id": tenant_id,
            "chunk_index": idx,
            "content_snippet": ch[:1000],
            "embedding": vec
        }).execute()
    return email_id

def ingest_pull(upn: str, top: int = 25) -> int:
    supa = get_client()
    tenant_id = APP_TENANT_ID
    mailbox_id = _ensure_mailbox(supa, tenant_id, upn)
    msgs = list_messages(upn, top=top)
    for m in msgs:
        full = get_message(upn, m["id"])
        norm = normalize_graph_message(full)
        thread_id = _ensure_thread(supa, tenant_id, mailbox_id, full)
        upsert_email_with_embeddings(supa, tenant_id, mailbox_id, thread_id, norm)
    return len(msgs)
