from typing import List, Dict, Any
from app.rag import embed
from app.db import get_client
import os

APP_TENANT_ID = os.getenv("APP_TENANT_ID")

def search_emails(query: str, k: int = 8) -> List[Dict[str, Any]]:
    supa = get_client()
    q_vec = embed(query)
    res = supa.rpc("semantic_search_emails", {"tenant_in": APP_TENANT_ID, "query_vec": q_vec, "k": k}).execute()
    return res.data or []

def search_kb(query: str, k: int = 8) -> List[Dict[str, Any]]:
    supa = get_client()
    q_vec = embed(query)
    res = supa.rpc("semantic_search_kb", {"tenant_in": APP_TENANT_ID, "query_vec": q_vec, "k": k}).execute()
    return res.data or []
