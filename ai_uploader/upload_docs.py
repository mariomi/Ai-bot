import os
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# --- CONFIGURAZIONE ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inizializza i client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ Client Supabase e OpenAI inizializzati con successo.")
except Exception as e:
    print(f"❌ Errore durante l'inizializzazione dei client: {e}")
    exit()

def process_and_upload(file_path: str, table_name: str = "documents"):
    """
    Legge un file, lo divide in chunks, crea embeddings e carica tutto su Supabase.
    """
    print(f"⏳ Inizio elaborazione del file: {file_path}")

    # 1. Carica il documento usando LangChain
    loader = TextLoader(file_path, encoding='utf-8')
    documents = loader.load()

    # 2. Suddivide il testo in pezzi più piccoli (chunks)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"📄 Documento diviso in {len(chunks)} chunks.")

    # 3. Itera su ogni chunk, crea l'embedding e lo carica su Supabase
    for i, chunk in enumerate(chunks):
        try:
            content = chunk.page_content

            # Chiama l'API di OpenAI per trasformare il testo in un vettore numerico
            print(f"🧠 Creazione embedding per il chunk {i+1}/{len(chunks)}...")
            embedding_response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=content
            )
            embedding = embedding_response.data[0].embedding

            # Prepara i dati da inserire nel database
            data_to_insert = {
                "content": content,
                "embedding": embedding
            }

            # Inserisce i dati nella tabella di Supabase
            print(f"⬆️ Caricamento del chunk {i+1} su Supabase...")
            supabase.table(table_name).insert(data_to_insert).execute()

        except Exception as e:
            print(f"❌ ERRORE durante l'elaborazione del chunk {i+1}: {e}")
            continue
    
    print("✅ Elaborazione e caricamento completati con successo!")


if __name__ == "__main__":
    file_da_caricare = "documento.txt"
    process_and_upload(file_da_caricare)