import json
from typing import List, Dict, Any
from app.rag import chat
from app.semantic import search_emails

def get_insights(k:int=30) -> Dict[str, Any]:
    hits = search_emails("azioni urgenti clienti pagamenti scadenze", k=k)
    prompt = [
        {"role":"system","content":"Analizza gli snippet email e restituisci JSON con: urgent_items[], risks[], followups[], recurring_topics[]"},
        {"role":"user","content": json.dumps([{"subject":h.get("subject"),"snippet":h.get("snippet")} for h in hits], ensure_ascii=False)}
    ]
    raw = chat(prompt, temperature=0)
    try:
        data = json.loads(raw)
    except Exception:
        data = {"urgent_items":[], "risks":[], "followups":[], "recurring_topics":[]}
    return {"insights": data, "sample": hits[:5]}
