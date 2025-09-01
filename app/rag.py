import os, json
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from app.openai_client import get_openai
from app.utils import html_to_text

EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

client = get_openai()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def embed(text: str) -> List[float]:
    text = (text or "")[:8000]
    resp = client.embeddings.create(model=EMBED_MODEL, input=text)
    return resp.data[0].embedding

def build_qa_prompt(question: str, passages: List[Dict[str, Any]]):
    ctx = []
    for p in passages:
        ctx.append(
            f"FROM: {p.get('from_address')}\n"
            f"RECEIVED: {p.get('received_at')}\n"
            f"SUBJECT: {p.get('subject')}\n"
            f"SNIPPET: {(p.get('snippet') or p.get('body_text',''))[:1000]}"
        )
    system = (
        "Sei un assistente per Q&A su email e knowledge base. "
        "Rispondi SOLO usando i PASSAGGI forniti. Se l'informazione non emerge, dì: 'Non emerge dai dati indicizzati.'"
    )
    user = "DOMANDA: " + question + "\n\nPASSAGGI:\n" + "\n\n---\n\n".join(ctx)
    return [{"role":"system","content":system},{"role":"user","content":user}]

def build_summary_prompt(emails: List[Dict[str, Any]], instruction: str):
    ctx = []
    for e in emails:
        ctx.append(f"[{e.get('received_at')}] {e.get('from_address')} — {e.get('subject')}\n{(e.get('snippet') or e.get('body_text',''))[:600]}")
    system = "Sei un assistente che sintetizza email in modo accurato e azionabile."
    user = "EMAILS:\n\n" + "\n\n---\n\n".join(ctx) + "\n\nISTRUZIONI:\n" + instruction
    return [{"role":"system","content":system},{"role":"user","content":user}]

def chat(messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
    resp = client.chat.completions.create(model=CHAT_MODEL, temperature=temperature, messages=messages)
    return resp.choices[0].message.content
