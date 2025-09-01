# AI Email & Personal Assistant (FastAPI + Supabase + OpenAI)

**Questo repo è operativo** (non solo un report). Usa **OpenAI** standard.

## Setup rapido
1. Supabase (EU consigliata). Applica `sql/001..004` in ordine.
2. `.env` da `.env.example` (compila: `OPENAI_API_KEY`, Supabase, Graph, `APP_TENANT_ID`).
3. Avvio locale:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   make run
   ```
4. Oppure Docker:
   ```bash
   docker compose up --build
   ```

## Endpoints
- `POST /ingest/pull?user_upn=<UPN>`
- `POST /query`
- `POST /summarize`
- `GET /insights`
- `POST /kb/upload` (PDF multipart)
- `POST /assistant/chat`
- `POST /assistant/extract_tasks`
- `POST /assistant/task`

Importa `postman/ai-email-assistant.postman_collection.json` per test veloci.


## Come "addestrare" con il tuo materiale (RAG)
Puoi indicizzare i tuoi documenti nella **Knowledge Base**:
- Singolo PDF: `POST /kb/upload` (multipart)
- **Bulk**: `POST /kb/upload-zip` con uno ZIP che contiene `.pdf, .md, .txt, .html, .docx`
- **CLI**: `python scripts/ingest_folder.py -d ./miei_documenti`

Poi interroga:
- Solo KB: `GET /kb/search?q=...&k=8`
- Chat ibrida (Email+KB): `POST /assistant/chat` con `{"message":"..."}`

> Nota: questo approccio è **retrieval-augmented** (RAG). Per esigenze di stile/formatting specifico, valuterai eventualmente **fine-tuning** su set piccoli di esempi (non necessario per ricordare fatti).

