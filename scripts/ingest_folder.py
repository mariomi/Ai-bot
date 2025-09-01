#!/usr/bin/env python3
import os, argparse, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add project root to path

from app.kb import ingest_file

def main():
    parser = argparse.ArgumentParser(description="Ingesta ricorsiva di documenti nella KB")
    parser.add_argument("-d","--dir", required=True, help="Cartella radice")
    args = parser.parse_args()

    supported = {".pdf",".md",".txt",".html",".htm",".docx"}
    count = 0
    for root, _, files in os.walk(args.dir):
        for f in files:
            if os.path.splitext(f)[1].lower() in supported:
                full = os.path.join(root, f)
                doc_id = ingest_file(full, title=os.path.relpath(full, args.dir), source=full)
                if doc_id:
                    count += 1
                    print(f"[OK] {full} -> {doc_id}")
                else:
                    print(f"[SKIP] {full}")
    print(f"Totale documenti ingestiti: {count}")

if __name__ == "__main__":
    main()
