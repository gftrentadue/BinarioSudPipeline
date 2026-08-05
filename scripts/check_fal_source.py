#!/usr/bin/env python3
"""Controllo leggero sulla fonte FAL: nessun OCR, nessuna scrittura di dati
GTFS. Risolve dalla pagina indice il PDF del quadro orario "Da e per Bari"
attualmente in vigore (il nome del file cambia a ogni pubblicazione), ne
calcola lo sha256 e lo confronta con l'ultimo hash noto in
data/fal_source_state.json.

Se cambia: aggiorna lo stato e segnala il cambiamento su stdout / GITHUB_OUTPUT
(il workflow, non questo script, apre eventualmente una issue — qui non viene
mai pubblicato o scritto nulla in assets/ o in build_gtfs.py)."""
import hashlib, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_PATH = os.path.join(ROOT, "data", "fal_source_state.json")
INDEX_URL = "https://ferrovieappulolucane.it/tratta/orari/"
LINK_RE = re.compile(r'<a href="([^"]+\.pdf)"[^>]*>([^<]*MODUGNO[^<]*)</a>', re.IGNORECASE)

HEADERS = {"User-Agent": "Mozilla/5.0 (BinarioSudPipeline FAL source check)"}


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def resolve_pdf_url():
    index_html = fetch(INDEX_URL).decode("utf-8", errors="replace")
    m = LINK_RE.search(index_html)
    if not m:
        raise RuntimeError("Link al PDF 'Da e per Bari' non trovato nella pagina indice FAL: "
                            "la struttura della pagina potrebbe essere cambiata, verificare a mano.")
    return m.group(1)


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"pdf_url": None, "sha256": None}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_github_output(changed, pdf_url, old_url, old_sha, new_sha):
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(f"changed={'true' if changed else 'false'}\n")
        f.write(f"pdf_url={pdf_url}\n")
        f.write(f"old_pdf_url={old_url or ''}\n")
        f.write(f"old_sha256={old_sha or ''}\n")
        f.write(f"new_sha256={new_sha}\n")


def main():
    pdf_url = resolve_pdf_url()
    print(f"PDF corrente: {pdf_url}")

    pdf_bytes = fetch(pdf_url, timeout=60)
    new_sha = hashlib.sha256(pdf_bytes).hexdigest()

    state = load_state()
    old_url, old_sha = state.get("pdf_url"), state.get("sha256")
    changed = (new_sha != old_sha) or (pdf_url != old_url)

    if changed:
        print(f"CAMBIAMENTO RILEVATO: url {old_url!r} -> {pdf_url!r}, "
              f"sha256 {old_sha!r} -> {new_sha!r}")
        save_state({"pdf_url": pdf_url, "sha256": new_sha})
    else:
        print("Nessun cambiamento rispetto all'ultima verifica nota.")

    write_github_output(changed, pdf_url, old_url, old_sha, new_sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
