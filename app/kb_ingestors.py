import os
from typing import Optional
from bs4 import BeautifulSoup
from pypdf import PdfReader
from docx import Document

def read_text_from_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return read_pdf(path)
    if ext in [".md", ".txt"]:
        return read_text(path)
    if ext in [".html", ".htm"]:
        return read_html(path)
    if ext in [".docx"]:
        return read_docx(path)
    # Unsupported -> empty
    return ""

def read_pdf(path: str) -> str:
    text = ""
    reader = PdfReader(path)
    for p in reader.pages:
        text += (p.extract_text() or "") + "\n"
    return text

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def read_html(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","noscript"]):
        tag.decompose()
    return soup.get_text("\n")

def read_docx(path: str) -> str:
    doc = Document(path)
    paras = [p.text for p in doc.paragraphs]
    return "\n".join(paras)
