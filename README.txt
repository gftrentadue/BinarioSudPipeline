GTFS Modugno <-> Bari  -  Rilascio v2
=====================================
feed_version: 20260618-7   (sostituisce v1 20260612-1; patch accessibilita' FAL su 20260618-6)
Validita': FAL 27/10/2025-12/12/2026 ; Trenitalia 14/06/2026-12/12/2026

CONTENUTO
- 2 operatori (FAL, Trenitalia), 4 stazioni con coordinate
- 99 corse / 198 stop_times:
    FAL  : 40 (20 Bari->Modugno + 20 Modugno->Bari), feriale Lun-Sab
    TI   : 59 (29 Modugno->Bari + 30 Bari->Modugno), pattern multipli
- Campi GTFS nativi per-corsa (valori GTFS: 0=ignoto, 1=si, 2=no):
    bikes_allowed         : 1 per tutte le corse (FAL confermato da sito FAL; TI documentato)
    wheelchair_accessible : TI = 1 (carrozza attrezzata documentata)
                            FAL = 2 (ASSUNTO non accessibile: nessun dato, da verificare)
- Calendario: 8 service_id + motore festivita' nazionali italiane
  (nei festivi infrasettimanali i feriali sono rimossi e i festivi attivati)

BUNDLE NELL'APP FLUTTER
- Copiare assets/gtfs/*.txt nella cartella assets/gtfs/ del progetto
- Dichiarare assets/gtfs/ in pubspec.yaml
- L'app determina se una corsa e' attiva in una data leggendo
  calendar.txt + calendar_dates.txt (unica fonte di verita').

ATTRIBUTI ESTESI (non-GTFS)
- Categoria treno (R/RV), garanzia sciopero (G), prenotazione,
  binario, fermata intermedia, nota di circolazione: nei side-car JSON
  ti_modugno_bari_attributes.json e ti_bari_modugno_attributes.json
  (consegnati separatamente), agganciabili via trip_id/train_number.

PUNTI APERTI (da rivedere periodicamente)
- FAL_end (12/12/2026): ASSUNTO, nessuna scadenza pubblicata -> riverificare
- Accessibilita' carrozzina FAL: ASSUNTA non accessibile (wheelchair_accessible=2),
  nessun dato sul sito FAL -> verificare e correggere in 1 se confermata accessibile
- Festivita' locali/patronali: NON modellate (treni assunti circolanti)
- platform_bari_centrale nel side-car: lettura OCR best-effort, da verificare

Generato da build_gtfs.py (riproducibile).
