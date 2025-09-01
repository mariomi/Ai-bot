import os, math, zipfile, tempfile
from typing import Optional, List
from app.db import get_client
from app.rag import embed
from app.kb_ingestors import read_text_from_file

APP_TENANT_ID = os.getenv("APP_TENANT_ID")

def _chunk_text(text: str, max_len: int = 1200, overlap: int = 150):
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i+max_len]
        chunks.append(chunk)
        i += max_len - overlap
    return chunks

def ingest_text(text: str, title: str, source: str, mime_type: str = "text/plain", tags: Optional[List[str]] = None) -> str:
    supa = get_client()
    doc = supa.table("kb_documents").insert({
        "tenant_id": APP_TENANT_ID,
        "title": title,
        "source": source,
        "mime_type": mime_type
    }).execute().data[0]
    chunks = _chunk_text(text)
    for idx, ch in enumerate(chunks):
        vec = embed(ch)
        supa.table("kb_chunks").insert({
            "doc_id": doc["id"],
            "tenant_id": APP_TENANT_ID,
            "chunk_index": idx,
            "content": ch,
            "embedding": vec
        }).execute()
    return doc["id"]

def ingest_file(filepath: str, title: Optional[str] = None, source: Optional[str] = None) -> str:
    text = read_text_from_file(filepath)
    if not text.strip():
        return ""
    name = title or os.path.basename(filepath)
    src = source or filepath
    ext = os.path.splitext(filepath)[1].lower()
    mime = {
        ".pdf": "application/pdf",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".html": "text/html",
        ".htm": "text/html",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }.get(ext, "text/plain")
    return ingest_text(text, title=name, source=src, mime_type=mime)

def ingest_zip(zip_path: str) -> int:
    count = 0
    with zipfile.ZipFile(zip_path, "r") as z:
        with tempfile.TemporaryDirectory() as tmpd:
            z.extractall(tmpd)
            for root, _, files in os.walk(tmpd):
                for f in files:
                    p = os.path.join(root, f)
                    if os.path.splitext(p)[1].lower() in [".pdf",".md",".txt",".html",".htm",".docx"]:
                        doc_id = ingest_file(p, title=os.path.relpath(p, tmpd), source=f"zip:{os.path.basename(zip_path)}")
                        if doc_id: count += 1
    return count
