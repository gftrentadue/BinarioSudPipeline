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
  binario, fermata intermedia, nota di circolazione: nei 4 side-car JSON
  in assets/attributes/ (ti_bari_modugno, ti_modugno_bari, fal_bari_modugno,
  fal_modugno_bari _attributes.json), versionati in questo repo e agganciabili
  via trip_id.
- Da ora sono generati/pubblicati anche da questa pipeline (non piu' "consegnati
  separatamente"): scripts/package_release.py li impacchetta in
  attributes-<feed_version>.zip, un asset di release distinto da
  gtfs-<feed_version>.zip ma con lo stesso feed_version (stessa release/tag),
  cosi' i trip_id restano sempre coerenti tra i due zip.

PUBBLICAZIONE (dist/, generato da scripts/package_release.py, non versionato)
- gtfs-<feed_version>.zip        : assets/gtfs/*.txt
- attributes-<feed_version>.zip  : assets/attributes/*.json
- manifest.json (contratto Fase 2 spec SS1.3/SS1.4), schema_version: 2
  - feed_url, feed_size_bytes, feed_sha256           -> per gtfs-<feed_version>.zip
  - attributes_url, attributes_size_bytes, attributes_sha256 -> per attributes-<feed_version>.zip
  - schema_version alzato da 1 a 2 con l'introduzione di questi 3 nuovi campi
    (breaking change deliberato, per policy di progetto: qualunque estensione del
    manifest incrementa schema_version, anche quando i campi sono additivi).
    ATTENZIONE: l'app BinarioSud gia' installata verifica schemaVersion in
    FeedRefreshService (supportedSchemaVersion = 1) e smette di aggiornare il GTFS
    da rete (RF-07) finche' non viene rilasciato un aggiornamento dell'app che
    riconosce schema_version 2 -- effetto collaterale noto e accettato.
- Pubblicati insieme da .github/workflows/publish.yml (workflow_dispatch manuale),
  come asset della stessa GitHub Release, resa pubblica solo a upload completato.

LATO APP (fuori scope di questo repo, da fare in BinarioSud)
- lib/data/feed_manifest.dart: aggiungere attributesUrl/attributesSizeBytes/
  attributesSha256 (nullable, stesso pattern dei campi feed_*).
- lib/data/feed_refresh_service.dart: alzare supportedSchemaVersion a 2 e
  aggiungere il download/verifica/estrazione di attributes-<feed_version>.zip,
  analogo a _downloadAndSwap per il GTFS.
- lib/data/attributes_parser.dart: nessuna modifica di formato attesa (stesso
  schema {meta, trains[]} gia' consumato dal bundle locale).

VERIFICA PERIODICA DELLE FONTI ORARIO (controllo, non scraping automatico)
Indagine: ne' RFI ne' FAL pubblicano oggi un GTFS o un'API aperta per questa
tratta (verificato su dati.puglia.it, dati.gov.it, Mobility Database/Transitland
ad agosto 2026: il dataset FAL su dati.puglia.it e' fermo al 2021, quello TI
si ferma al 2024, nessun GTFS RFI-derivato pubblicato per la Puglia). I dati
restano quindi accentrati in build_gtfs.py, ma il *metodo di aggiornamento*
e' cambiato:
- data/ti_trains.json: le tabelle corse TI (num/orari/pattern), prima literal
  Python dentro build_gtfs.py, ora vivono qui; build_gtfs.py le importa senza
  altre modifiche di logica.
- scripts/update_ti_source.py: legge i quadri orario RFI live (pagine HTML
  server-side, senza login/JS, per Bari Centrale id=550 e Modugno id=43609223)
  e aggiorna SOLO data/ti_trains.json. Se una corsa e' nuova o cambia orario,
  il pattern di calendario viene scritto come sentinella "DA_CLASSIFICARE"
  (mai indovinato automaticamente): build_gtfs.py fallisce apposta con
  KeyError su PAT2SERVICE finche' non lo si classifica a mano. Eseguito dal
  workflow schedulato .github/workflows/check_ti_source.yml (mensile), che
  apre una Pull Request se ci sono differenze -- nessun commit/pubblicazione
  automatica, revisione via git diff prima del merge.
- scripts/check_fal_source.py + data/fal_source_state.json: nessun OCR. Solo
  hash sha256 del PDF "Da e per Bari" attualmente pubblicato da FAL (il nome
  file cambia a ogni pubblicazione, risolto dalla pagina indice), confrontato
  con l'ultimo hash noto. Se cambia, .github/workflows/check_fal_source.yml
  (mensile) apre una issue di notifica (mai il contenuto del PDF, per la
  clausola di non redistribuzione nei Termini RFI/FAL) -- controllo e
  trascrizione restano manuali come oggi.
- Entrambi i workflow sono separati da publish.yml, che resta l'unico modo
  per pubblicare una Release ed e' e rimane manuale (workflow_dispatch).

PUNTI APERTI (da rivedere periodicamente)
- FAL_end (12/12/2026): ASSUNTO, nessuna scadenza pubblicata -> riverificare
- Accessibilita' carrozzina FAL: ASSUNTA non accessibile (wheelchair_accessible=2),
  nessun dato sul sito FAL -> verificare e correggere in 1 se confermata accessibile
- Festivita' locali/patronali: NON modellate (treni assunti circolanti)
- platform_bari_centrale nel side-car: lettura OCR best-effort, da verificare

Generato da build_gtfs.py (riproducibile).
