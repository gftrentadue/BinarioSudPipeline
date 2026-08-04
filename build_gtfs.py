#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generatore GTFS - versione iterativa, feed_version 20260618-7
Slice incluse:
  - [FAL, Bari Centrale <-> Modugno]      (20+20 corse, FERIALE Lun-Sab)
  - [TI, Modugno -> Bari Centrale]        (29 corse, pattern multipli)
Novita' di questa versione:
  - agency/stops/route Trenitalia + 29 trips TI (direction_id=0)
  - campi GTFS nativi bikes_allowed e wheelchair_accessible in trips.txt
  - motore FESTIVITA' NAZIONALI italiane: rimuove i servizi feriali e attiva
    quelli festivi nei giorni di festa infrasettimanali (calendar_dates)
  - calendari namespaced per operatore (FAL_* / TI_*)

Convenzioni: direction_id 0=verso Bari, 1=verso Modugno; route_type=2 (rail).
Provenienza date (per i controlli periodici dell'utente):
  FAL_start 27/10/2025 = DOCUMENTATO (manifesto in vigore)
  FAL_end   12/12/2026 = ASSUNTO     (nessuna scadenza pubblicata, da riverificare)
  TI_start  14/06/2026 = DOCUMENTATO (quadro orario RFI)
  TI_end    12/12/2026 = DOCUMENTATO (quadro orario RFI)
Festivita' locali (patronali Bari/Modugno) = NON gestite: si assume che i treni
circolino (decisione utente, da rivalutare in futuro).
"""
import csv, os, datetime

OUT = os.path.join(os.path.dirname(__file__), "assets", "gtfs")
os.makedirs(OUT, exist_ok=True)

FEED_VERSION = "20260618-7"
FAL_START, FAL_END = "20251027", "20261212"
TI_START,  TI_END  = "20260614", "20261212"

def hhmm(h, m): return f"{h:02d}:{m:02d}:00"
def t(s):
    h, m = s.split("."); return int(h), int(m)

# =====================================================================
# DATI FAL  (service_id namespaced)
# =====================================================================
# verso Modugno (direction_id=1): (bari_h,bari_m, mod_h,mod_m, train_no, service)
FAL_TRIPS_M = [
    (4,14, 4,34, None, "FAL_FERIALE"), (5,6, 5,26, None, "FAL_FERIALE"),
    (6,17, 6,37, None, "FAL_FERIALE"), (7,49, 8,11, None, "FAL_FERIALE"),
    (9,59,10,21, None, "FAL_FERIALE"), (10,48,11,9, None, "FAL_FERIALE"),
    (11,39,12,1, None, "FAL_FERIALE"), (12,44,13,6, None, "FAL_FERIALE"),
    (13,39,14,1, None, "FAL_FERIALE"), (14,9,14,29, None, "FAL_FERIALE"),
    (15,18,15,38,None, "FAL_FERIALE"), (16,0,16,22, None, "FAL_FERIALE"),
    (16,55,17,17,None, "FAL_FERIALE"), (17,43,18,4,"129","FAL_FERIALE_NO_AGO"),
    (18,9,18,29, None, "FAL_FERIALE"), (19,17,19,37,None,"FAL_FERIALE"),
    (20,3,20,23, None, "FAL_FERIALE"), (20,59,21,20,None,"FAL_FERIALE"),
    (21,22,21,42,None, "FAL_FERIALE"), (22,10,22,30,None,"FAL_FERIALE"),
]
# verso Bari (direction_id=0): (mod_h,mod_m, bari_h,bari_m, train_no, service)
FAL_TRIPS_B = [
    (5,44, 6,3,  None, "FAL_FERIALE"), (6,56, 7,15, None, "FAL_FERIALE"),
    (7,16, 7,35, None, "FAL_FERIALE"), (7,45, 8,5,  None, "FAL_FERIALE"),
    (8,30, 8,49, None, "FAL_FERIALE"), (9,21, 9,40, None, "FAL_FERIALE"),
    (9,55,10,15, None, "FAL_FERIALE"), (10,40,11,1, None, "FAL_FERIALE"),
    (11,31,11,52,"116","FAL_FERIALE_NO_AGO"), (12,40,13,0, None,"FAL_FERIALE"),
    (13,35,13,55,None, "FAL_FERIALE"), (14,49,15,8, None, "FAL_FERIALE"),
    (15,56,16,16,None, "FAL_FERIALE"), (16,51,17,11,None, "FAL_FERIALE"),
    (17,35,17,56,None, "FAL_FERIALE"), (18,47,19,9, None, "FAL_FERIALE"),
    (19,55,20,17,None, "FAL_FERIALE"), (20,51,21,12,None, "FAL_FERIALE"),
    (22,3,22,24, None, "FAL_FERIALE"), (22,51,23,10,None, "FAL_FERIALE"),
]

# =====================================================================
# DATI TI  Modugno -> Bari Centrale (direction_id=0)
# (num, dep "H.MM", arr "H.MM", pattern)
# =====================================================================
PAT2SERVICE = {
    "MON_FRI": "TI_FER_LUNVEN", "MON_SAT": "TI_FER_LUNSAB",
    "SAT_SUN_HOL": "TI_FEST_SAB", "SAT_ONLY_SUMMER_GAP": "TI_SAB_GAP",
    "SAT_ONLY_EXCL_AUG": "TI_SAB_EXCL_AUG",   # solo treno 19863: sabati, escl. 8 e 15 ago
    "DAILY": "TI_GIORNAL",
}
# TI Modugno -> Bari Centrale (direction_id=0): (num, dep_modugno, arr_bari, pattern)
TI_TRAINS_MB = [
    ("19826","5.37","5.50","MON_SAT"), ("19828","6.37","6.50","MON_SAT"),
    ("19872","7.26","7.39","SAT_SUN_HOL"), ("19854","7.27","7.40","MON_FRI"),
    ("23602","7.59","8.15","MON_FRI"), ("19874","8.17","8.30","MON_SAT"),
    ("23604","8.59","9.15","MON_FRI"), ("19876","9.05","9.18","SAT_SUN_HOL"),
    ("23606","10.59","11.15","MON_FRI"), ("19878","11.05","11.18","SAT_SUN_HOL"),
    ("19836","12.37","12.50","MON_FRI"), ("19880","12.44","12.57","MON_SAT"),
    ("19838","14.02","14.15","MON_FRI"), ("19882","14.05","14.18","MON_SAT"),
    ("19884","14.47","15.00","SAT_SUN_HOL"), ("23608","14.59","15.15","MON_FRI"),
    ("19886","15.47","16.00","MON_SAT"), ("23610","15.59","16.15","MON_FRI"),
    ("19890","16.27","16.40","SAT_SUN_HOL"), ("23612","16.59","17.15","MON_FRI"),
    ("19892","17.59","18.12","SAT_SUN_HOL"), ("23614","17.59","18.15","MON_FRI"),
    ("23616","18.59","19.15","MON_FRI"), ("19894","19.21","19.35","MON_SAT"),
    ("23618","19.59","20.15","MON_FRI"), ("19896","20.32","20.45","SAT_SUN_HOL"),
    ("23620","20.59","21.15","MON_FRI"), ("19898","21.22","21.35","SAT_ONLY_SUMMER_GAP"),
    ("19852","22.07","22.20","DAILY"),
]

# TI Bari Centrale -> Modugno (direction_id=1): (num, dep_bari, arr_modugno, pattern)
TI_TRAINS_BM = [
    ("19825","5.30","5.42","MON_SAT"), ("19827","6.10","6.22","MON_SAT"),
    ("23603","6.45","6.58","MON_FRI"), ("19871","7.18","7.30","SAT_SUN_HOL"),
    ("23605","7.45","7.58","MON_FRI"), ("19853","9.10","9.22","MON_FRI"),
    ("19873","9.50","10.02","MON_SAT"), ("19875","10.50","11.02","SAT_SUN_HOL"),
    ("19831","11.10","11.22","MON_FRI"), ("23607","12.45","12.58","MON_FRI"),
    ("19877","13.10","13.22","SAT_ONLY_SUMMER_GAP"), ("19879","13.40","13.52","SAT_SUN_HOL"),
    ("23609","13.45","13.58","MON_FRI"), ("19881","14.40","14.52","SAT_SUN_HOL"),
    ("23611","14.45","14.58","MON_FRI"), ("19883","15.24","15.36","SAT_ONLY_SUMMER_GAP"),
    ("23613","15.45","15.58","MON_FRI"), ("19891","16.30","16.42","SAT_SUN_HOL"),
    ("23615","16.45","16.58","MON_FRI"), ("19893","17.44","17.56","SAT_ONLY_SUMMER_GAP"),
    ("23617","17.45","17.58","MON_FRI"), ("19895","18.20","18.33","SAT_SUN_HOL"),
    ("23619","18.45","18.58","MON_FRI"), ("19897","19.45","19.57","SAT_SUN_HOL"),
    ("23621","19.45","19.58","MON_FRI"), ("19899","20.50","21.02","MON_SAT"),
    ("19849","21.10","21.22","MON_FRI"), ("19885","21.28","21.40","SAT_SUN_HOL"),
    ("19851","22.45","22.57","MON_FRI"), ("19863","23.37","23.49","SAT_ONLY_EXCL_AUG"),
]

def w(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)

# ---------- agency ----------
w("agency.txt", ["agency_id","agency_name","agency_url","agency_timezone","agency_lang"],
  [["FAL","Ferrovie Appulo Lucane","https://www.ferrovieappulolucane.it","Europe/Rome","it"],
   ["TI","Trenitalia","https://www.trenitalia.com","Europe/Rome","it"]])

# ---------- stops ----------
STOP_COORDS = {
    "BARI_TI":  ("41.1176638","16.8693885"), "MOD_TI": ("41.0719215","16.785155"),
    "BARI_FAL": ("41.118585","16.8684559"),   "MOD_FAL":("41.0864698","16.7792309"),
}
STOPS = [
    ("BARI_FAL","Bari Centrale (FAL)"), ("MOD_FAL","Modugno Città"),
    ("BARI_TI","Bari Centrale (Trenitalia)"), ("MOD_TI","Modugno"),
]
w("stops.txt", ["stop_id","stop_name","stop_lat","stop_lon"],
  [[sid,name,STOP_COORDS[sid][0],STOP_COORDS[sid][1]] for sid,name in STOPS])

# ---------- routes ----------
w("routes.txt", ["route_id","agency_id","route_short_name","route_long_name","route_type"],
  [["FAL_BA_MT","FAL","","Bari Centrale - Matera Centrale","2"],
   ["TI_BA_TA","TI","","Bari Centrale - Taranto","2"]])

# ---------- trips + stop_times ----------
trips_rows = []; st_rows = []
def add_trip(trip_id, route_id, service, headsign, short, direction,
             a_id, a_h, a_m, b_id, b_h, b_m, bikes, wheel):
    trips_rows.append([route_id, service, trip_id, headsign, short, direction, bikes, wheel])
    st_rows.append([trip_id, hhmm(a_h,a_m), hhmm(a_h,a_m), a_id, "1"])
    st_rows.append([trip_id, hhmm(b_h,b_m), hhmm(b_h,b_m), b_id, "2"])

# FAL verso Modugno (BARI_FAL -> MOD_FAL)
for (bh,bm,mh,mm,num,svc) in FAL_TRIPS_M:
    add_trip(f"FAL_M_{bh:02d}{bm:02d}","FAL_BA_MT",svc,"Modugno",num or "","1",
             "BARI_FAL",bh,bm,"MOD_FAL",mh,mm,"1","2")
# FAL verso Bari (MOD_FAL -> BARI_FAL)
for (mh,mm,bh,bm,num,svc) in FAL_TRIPS_B:
    add_trip(f"FAL_B_{mh:02d}{mm:02d}","FAL_BA_MT",svc,"Bari Centrale",num or "","0",
             "MOD_FAL",mh,mm,"BARI_FAL",bh,bm,"1","2")
# TI verso Bari (MOD_TI -> BARI_TI)  trip_id = TI_<num> (univoco)
for (num,dep,arr,pat) in TI_TRAINS_MB:
    dh,dm = t(dep); ah,am = t(arr)
    add_trip(f"TI_{num}","TI_BA_TA",PAT2SERVICE[pat],"Bari Centrale",num,"0",
             "MOD_TI",dh,dm,"BARI_TI",ah,am,"1","1")
# TI verso Modugno (BARI_TI -> MOD_TI)  trip_id = TI_<num> (univoco)
for (num,dep,arr,pat) in TI_TRAINS_BM:
    dh,dm = t(dep); ah,am = t(arr)
    add_trip(f"TI_{num}","TI_BA_TA",PAT2SERVICE[pat],"Modugno",num,"1",
             "BARI_TI",dh,dm,"MOD_TI",ah,am,"1","1")

w("trips.txt", ["route_id","service_id","trip_id","trip_headsign","trip_short_name",
                "direction_id","bikes_allowed","wheelchair_accessible"], trips_rows)
w("stop_times.txt", ["trip_id","arrival_time","departure_time","stop_id","stop_sequence"], st_rows)

# ---------- calendar ----------
# monday..sunday flags
w("calendar.txt",
  ["service_id","monday","tuesday","wednesday","thursday","friday","saturday","sunday",
   "start_date","end_date"],
  [["FAL_FERIALE",       "1","1","1","1","1","1","0",FAL_START,FAL_END],
   ["FAL_FERIALE_NO_AGO","1","1","1","1","1","1","0",FAL_START,FAL_END],
   ["TI_FER_LUNVEN",     "1","1","1","1","1","0","0",TI_START,TI_END],
   ["TI_FER_LUNSAB",     "1","1","1","1","1","1","0",TI_START,TI_END],
   ["TI_FEST_SAB",       "0","0","0","0","0","1","1",TI_START,TI_END],
   ["TI_SAB_GAP",        "0","0","0","0","0","1","0",TI_START,TI_END],
   ["TI_SAB_EXCL_AUG",   "0","0","0","0","0","1","0",TI_START,TI_END],
   ["TI_GIORNAL",        "1","1","1","1","1","1","1",TI_START,TI_END]])

# ---------- calendar_dates ----------
def d(s): return datetime.datetime.strptime(s,"%Y%m%d").date()
def s(dt): return dt.strftime("%Y%m%d")

def easter(year):
    a=year%19; b=year//100; c=year%100; dd=b//4; e=b%4; f=(b+8)//25
    g=(b-f+1)//3; h=(19*a+b-dd-g+15)%30; i=c//4; k=c%4
    l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
    month=(h+l-7*m+114)//31; day=((h+l-7*m+114)%31)+1
    return datetime.date(year,month,day)

def italian_holidays(years):
    H={}
    for y in years:
        for (mo,da,name) in [(1,1,"Capodanno"),(1,6,"Epifania"),(4,25,"Liberazione"),
                             (5,1,"Festa del Lavoro"),(6,2,"Festa della Repubblica"),
                             (8,15,"Ferragosto"),(11,1,"Ognissanti"),(12,8,"Immacolata"),
                             (12,25,"Natale"),(12,26,"Santo Stefano")]:
            H[datetime.date(y,mo,da)]=name
        es=easter(y); H[es]="Pasqua"; H[es+datetime.timedelta(days=1)]="Lunedi dell'Angelo"
    return H

cd_rows = []

# (A) FAL: soppressione TUTTO agosto per i 2 treni soppressi (129/116)
dt=datetime.date(2026,8,1)
while dt.month==8:
    if dt.weekday()!=6:  # no domenica (gia' off nel calendar)
        cd_rows.append(["FAL_FERIALE_NO_AGO", s(dt), "2"])
    dt+=datetime.timedelta(days=1)

# (B) TI: gap estivo 09-21 ago per il treno 19898 (solo-sabato) -> sabato 15/08
cd_rows.append(["TI_SAB_GAP", "20260815", "2"])

# (B-bis) TI: treno 19863 (solo-sabato) NON circola l'8 e il 15 agosto (entrambi sabati)
cd_rows.append(["TI_SAB_EXCL_AUG", "20260808", "2"])
cd_rows.append(["TI_SAB_EXCL_AUG", "20260815", "2"])

# (C) FESTIVITA' NAZIONALI
# servizi feriali: (service_id, window, weekday_attivi)  -> rimozione type=2
FERIALI = [
    ("FAL_FERIALE",        (FAL_START,FAL_END), set(range(0,6))),  # Lun-Sab
    ("FAL_FERIALE_NO_AGO", (FAL_START,FAL_END), set(range(0,6))),  # Lun-Sab
    ("TI_FER_LUNVEN",      (TI_START,TI_END),   set(range(0,5))),  # Lun-Ven
    ("TI_FER_LUNSAB",      (TI_START,TI_END),   set(range(0,6))),  # Lun-Sab
]
holidays = italian_holidays([2025,2026])
for hd in sorted(holidays):
    wd = hd.weekday()  # 0=Lun..6=Dom
    # rimozioni servizi feriali
    for sid,(ws,we),days in FERIALI:
        if d(ws) <= hd <= d(we) and wd in days:
            if sid=="FAL_FERIALE_NO_AGO" and hd.month==8:
                continue  # gia' rimosso dalla soppressione agosto (A)
            cd_rows.append([sid, s(hd), "2"])
    # attivazione servizio festivo TI nelle feste infrasettimanali (Lun-Ven)
    if d(TI_START) <= hd <= d(TI_END) and wd in set(range(0,5)):
        cd_rows.append(["TI_FEST_SAB", s(hd), "1"])

# ordinamento stabile
cd_rows.sort(key=lambda r:(r[0], r[1]))
w("calendar_dates.txt", ["service_id","date","exception_type"], cd_rows)

# ---------- feed_info ----------
w("feed_info.txt",
  ["feed_publisher_name","feed_publisher_url","feed_lang","feed_version",
   "feed_start_date","feed_end_date"],
  [["Progetto orari Modugno-Bari (personale)","https://example.com","it",
    FEED_VERSION, FAL_START, TI_END]])

print("Generato feed", FEED_VERSION)
print("trips:", len(trips_rows), "| stop_times:", len(st_rows),
      "| calendar_dates:", len(cd_rows))
