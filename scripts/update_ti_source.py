#!/usr/bin/env python3
"""Aggiorna data/ti_trains.json leggendo i quadri orario RFI (pagine HTML
server-side, senza login/JS) per Bari Centrale e Modugno.

Tocca SOLO data/ti_trains.json: non scrive mai in build_gtfs.py. Il file
risultante va rivisto con `git diff` prima di essere committato (nessuna
pubblicazione automatica).

Regola di selezione (identica alla curazione manuale attuale, vedi
assets/attributes/ti_*_attributes.json meta.schema_notes):
  - Modugno -> Bari Centrale: corse dalla pagina Partenze di Modugno la cui
    stazione di arrivo e' esattamente Bari Centrale (StationId 550).
  - Bari Centrale -> Modugno: corse dalla pagina Partenze di Bari Centrale
    che hanno Modugno (StationId 43609223) tra le fermate successive.

Per ogni corsa: se numero+orari coincidono con quanto gia' in
data/ti_trains.json, il pattern di calendario esistente viene mantenuto.
Se la corsa e' nuova o i suoi orari sono cambiati, il pattern viene scritto
come sentinella "DA_CLASSIFICARE": build_gtfs.py fallisce volutamente con
KeyError su PAT2SERVICE finche' non si classifica il pattern a mano (mai
indovinato automaticamente).
"""
import html, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "ti_trains.json")

BARI_CENTRALE_ID = "550"
MODUGNO_ID = "43609223"
BASE_URL = "https://prm.rfi.it/qo_prm/QO_Partenze_SiPMR.aspx"
SENTINEL = "DA_CLASSIFICARE"

CELL_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
ROW_RE = re.compile(r"<tr[^>]*>\s*<td class=\"cellauno center\".*?</tr>", re.DOTALL)
STOP_RE = re.compile(r'Id=(\d+)[^"]*">\s*([^<]+?)\s*</a>\s*\((\d{1,2}\.\d{2})\)')
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def fetch(station_id):
    url = f"{BASE_URL}?Id={station_id}&lin=&dalle=04.00&alle=23.59&ora=04.00&guid="
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (BinarioSudPipeline TI source check)"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", errors="replace")


def clean_text(html_fragment):
    stripped = TAG_RE.sub(" ", COMMENT_RE.sub("", html_fragment))
    return re.sub(r"\s+", " ", html.unescape(stripped)).strip()


def parse_periodicita(tail_html, train_num):
    marker = f"Treno {train_num} delle ore"
    idx = tail_html.find(marker)
    if idx == -1:
        return ""
    block = tail_html[idx: idx + 1500]
    m = re.search(r"Periodicit.*?</h5>(.*?)(?:<h5>|</div>\s*</div>\s*<div class=\"Dx\">)", block, re.DOTALL)
    if not m:
        return ""
    return clean_text(m.group(1)).strip(" *")


def parse_station_page(page_html):
    """Ritorna lista di dict: num, dep, dest_id, dest_name, arr, stops(list di
    (station_id, name, time)), note (testo periodicita' grezzo)."""
    trains = []
    for row_match in ROW_RE.finditer(page_html):
        row_html = row_match.group(0)
        cells = CELL_RE.findall(row_html)
        if len(cells) < 8:
            continue
        dep = clean_text(cells[0])
        if not re.match(r"^\d{1,2}\.\d{2}$", dep):
            continue
        num_m = re.search(r"/>\s*([A-Za-z0-9]+)\s*$", cells[1].strip())
        num = num_m.group(1).strip() if num_m else clean_text(cells[1])
        dest_m = re.search(r'Id=(\d+)[^"]*">\s*([^<]+?)\s*</a>\s*\((\d{1,2}\.\d{2})\)', cells[2])
        if not dest_m:
            continue
        dest_id, dest_name, arr = dest_m.group(1), dest_m.group(2).strip(), dest_m.group(3)
        stops_after = STOP_RE.findall(cells[7]) if len(cells) > 7 else []
        note = parse_periodicita(page_html[row_match.end():row_match.end() + 3000], num)
        trains.append({
            "num": num, "dep": dep, "dest_id": dest_id, "dest_name": dest_name,
            "arr": arr, "stops_after": stops_after, "note": note,
        })
    return trains


def strip_leading_zero(hhmm):
    h, m = hhmm.split(".")
    return f"{int(h)}.{m}"


def dep_minutes(entry):
    h, m = entry["dep"].split(".")
    return int(h) * 60 + int(m)


def build_mb(modugno_trains):
    """Modugno -> Bari Centrale: destinazione esattamente Bari Centrale."""
    out = []
    for tr in modugno_trains:
        if tr["dest_id"] == BARI_CENTRALE_ID:
            out.append({
                "num": tr["num"], "dep": strip_leading_zero(tr["dep"]),
                "arr": strip_leading_zero(tr["arr"]), "note": tr["note"],
            })
    return out


def build_bm(bari_trains):
    """Bari Centrale -> Modugno: Modugno tra le fermate successive."""
    out = []
    for tr in bari_trains:
        modugno_stop = next((s for s in tr["stops_after"] if s[0] == MODUGNO_ID), None)
        if modugno_stop:
            out.append({
                "num": tr["num"], "dep": strip_leading_zero(tr["dep"]),
                "arr": strip_leading_zero(modugno_stop[2]), "note": tr["note"],
            })
    return out


def merge(existing_list, fetched_list, direction_label):
    existing_by_num = {t["num"]: t for t in existing_list}
    merged = []
    report = []
    for tr in fetched_list:
        prev = existing_by_num.get(tr["num"])
        if prev and prev["dep"] == tr["dep"] and prev["arr"] == tr["arr"]:
            pattern = prev["pattern"]
        else:
            pattern = SENTINEL
            status = "NUOVO" if not prev else f"ORARIO CAMBIATO (prima {prev['dep']}->{prev['arr']})"
            report.append(f"  [{direction_label}] {tr['num']} {tr['dep']}->{tr['arr']} — {status}"
                          + (f' | nota RFI: "{tr["note"]}"' if tr["note"] else ""))
        merged.append({"num": tr["num"], "dep": tr["dep"], "arr": tr["arr"], "pattern": pattern})
    fetched_nums = {t["num"] for t in fetched_list}
    for num, prev in existing_by_num.items():
        if num not in fetched_nums:
            report.append(f"  [{direction_label}] {num} {prev['dep']}->{prev['arr']} — SPARITO dalla fonte RFI (rimosso)")
    return merged, report


def main():
    if not os.path.exists(DATA_PATH):
        print(f"ERRORE: {DATA_PATH} non trovato", file=sys.stderr)
        sys.exit(1)
    with open(DATA_PATH, encoding="utf-8") as f:
        current = json.load(f)

    print("Scarico quadro orario RFI Bari Centrale (partenze)...")
    bari_html = fetch(BARI_CENTRALE_ID)
    print("Scarico quadro orario RFI Modugno (partenze)...")
    modugno_html = fetch(MODUGNO_ID)

    bari_trains = parse_station_page(bari_html)
    modugno_trains = parse_station_page(modugno_html)
    print(f"Righe treno trovate: Bari Centrale={len(bari_trains)}, Modugno={len(modugno_trains)}")

    fetched_mb = build_mb(modugno_trains)
    fetched_bm = build_bm(bari_trains)
    print(f"Corse selezionate: Modugno->Bari={len(fetched_mb)}, Bari->Modugno={len(fetched_bm)}")

    merged_mb, report_mb = merge(current["modugno_bari"], fetched_mb, "Modugno->Bari")
    merged_bm, report_bm = merge(current["bari_modugno"], fetched_bm, "Bari->Modugno")

    current["modugno_bari"] = sorted(merged_mb, key=dep_minutes)
    current["bari_modugno"] = sorted(merged_bm, key=dep_minutes)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)
        f.write("\n")

    report = report_mb + report_bm
    if report:
        print("\nDifferenze rispetto ai dati precedenti (rivedi con `git diff data/ti_trains.json`):")
        print("\n".join(report))
        print(f"\n{len([r for r in report if 'SPARITO' not in r])} corse con pattern impostato a "
              f"'{SENTINEL}': classificale a mano in data/ti_trains.json prima di eseguire build_gtfs.py.")
    else:
        print("\nNessuna differenza: dati invariati rispetto all'ultima verifica.")


if __name__ == "__main__":
    main()
