"""Write malaysia_kpkt_smart_city.csv: the five pilot cities of the Malaysia Smart City Framework (2019) and the
councils rated under Penarafan Bandar Pintar Malaysia (2023 and 2024), both run by the housing and local government
ministry (KPKT, PLANMalaysia).

argv[1] = designations directory, argv[2] = data/raw/designations/sources.
Every list is parsed from the saved text of the official document (malaysia_saved/*.txt, made from the PDF or html
saved on 1 Nov 2026) and the script stops if a list or count differs from what the document prints.
"""
import csv, re, sys
from pathlib import Path

D, C = Path(sys.argv[1]), Path(sys.argv[2])
S = C / "malaysia_saved"
COLS = ["economy", "place_as_printed", "place_en", "area_as_printed", "area_scope",
        "project_id", "programme", "programme_model", "announcement_date", "date_precision",
        "first_treated_year", "batch", "source", "note"]
KPKT = "https://www.kpkt.gov.my/kpkt/resources/user_1/"
MSCF_ES = KPKT + "GALERI/PDF_PENERBITAN/FRAMEWORK/FRAMEWORK_SMART_CITY_EXECUTIVE_SUMMARY.pdf"
MM_2019 = ("https://www.malaymail.com/news/malaysia/2019/09/23/"
           "irda-smart-city-framework-a-big-step-to-realise-smart-nation-vision/1793389")
HPBS_2023 = KPKT + "media_akhbar/2023/SM_KOMITED_DALAM_PERANCANGAN_BANDAR_MALAYSIA_MADANI_KOMUNITI_SEJAHTERA.pdf"
MBPN_2024 = KPKT + "media_akhbar/2024/SM_MAJLIS_BANDAR_PINTAR_NEGARA_MEMPERKASAKAN_AGENDA_EKONOMI_MADANI.pdf"
HPBS_2024 = KPKT + "media_akhbar/2024/SM_HPBS_2024_AGENDA_BANDAR_MAMPAN_DAN_PINTAR.pdf"
MPKJ = ("https://www.mpkj.gov.my/index.php/ms/info-mpkj/pusat-media/arkib-berita/"
        "penarafan-bandar-pintar-smart-city-early-adopter-2023")
MBI = ("https://www.mbi.gov.my/pusat-media/aktiviti/"
       "tahniah-ipoh-antara-5-bandar-pintar-perintis-rangkul-status-smart-city-early-adopter-2023")
RATING = "Penarafan Bandar Pintar Malaysia (KPKT, PLANMalaysia)"
TYPE = {"Majlis Bandaraya": "City Council", "Majlis Perbandaran": "Municipal Council",
        "Majlis Daerah": "District Council", "Perbadanan": "Corporation"}


def text(name):
    return re.sub(r"[ \t]+", " ", (S / name).read_text(encoding="utf-8"))


def first_treated(date):
    y, m = int(date[:4]), int(date[5:7])
    return y if m <= 6 else y + 1


def council_en(printed):
    """English name of a council printed in Malay, e.g. Majlis Perbandaran Kulai -> Kulai Municipal Council."""
    for k, v in TYPE.items():
        if printed.startswith(k + " "):
            name = printed[len(k) + 1:]
            if name.endswith(" Bandaraya Pelancongan"):
                return f"{name[:-len(' Bandaraya Pelancongan')]} Municipal Council (Tourism City)"
            return f"{name} {v}"
    raise ValueError(printed)


rows = []

# 1. Malaysia Smart City Framework pilot cities. The executive summary names the five cities and their councils;
#    Bernama (via Malay Mail) dates the launch by the Prime Minister to 23 September 2019.
es = text("MSCF_executive_summary.txt")
flat = re.sub(r"\s+", " ", es)
assert ("Five (5) cities have been chosen as pilot project areas, namely Kuala Lumpur, Johor Bahru, "
        "Kota Kinabalu, Kuching, and Kulim.") in flat
mm = re.sub(r"\s+", " ", text("malaymail_2019-09-23.txt"))
assert "KUALA LUMPUR, Sept 23 ― The launch of the Malaysia Smart City Framework by Prime Minister" in mm
assert "First Published: Monday, 23 Sep 2019" in mm and "two-day Cities 4.0 Conference beginning today" in mm
PILOTS = [  # city, councils as printed in the executive summary, area as printed
    ("Kuala Lumpur", "Kuala Lumpur City Hall (KLCH)", "243 km²"),
    ("Johor Bahru", "Johor Bahru City Council (MBJB); Iskandar Puteri City Council (MBIP); "
                    "Pasir Gudang Municipal Council (MPPG)", "1,064 km2"),
    ("Kota Kinabalu", "Kota Kinabalu City Hall (KKCH)", "351 km²"),
    ("Kuching", "Kuching South City Council (KSCC); Kuching North City Hall (KNCH); Padawan City Council",
     "431.01 km²"),
    ("Kulim", "Kulim City Council; Kulim Hi-Tech Park (KHTP) local authority", "765km²"),
]
for i, (city, councils, area) in enumerate(PILOTS, 1):
    for c in councils.split("; "):
        assert c in flat, c
    assert f"Area: {area}" in flat, area
    ascn = city != "Kulim"
    rows.append({
        "economy": "Malaysia", "place_as_printed": city, "place_en": city, "area_as_printed": councils,
        "area_scope": "whole", "project_id": f"MY2019-MSCF-{i}",
        "programme": "Malaysia Smart City Framework pilot cities (KPKT)", "programme_model": "implementation support",
        "announcement_date": "2019-09-23", "date_precision": "day", "first_treated_year": first_treated("2019-09-23"),
        "batch": "MSCF pilot 2019",
        "source": f"MSCF executive summary p. 43-44, {MSCF_ES} (saved as MSCF_executive_summary.pdf); "
                  f"launch date: Bernama in Malay Mail 23 Sep 2019, {MM_2019} (saved as malaymail_2019-09-23.html)",
        "note": f"pilot area of {area} as printed, councils as printed; the framework gives each pilot city project "
                "implementation briefs with lead agencies and names no national funding"
                + ("; also an ASEAN Smart Cities Network pilot city (2018)" if ascn else "")})

# 2. Rating, 2023 round. KPKT's 9 November 2023 release counts 29 recipients but its list annex is not in the
#    saved PDF and no full list was found; two councils name themselves, and the two councils rated Tahap 2 in 2024
#    must have reached Tahap 1 in 2023, since only 2023 Tahap 1 councils could apply for Tahap 2 in 2024.
h23 = re.sub(r"\s+", " ", text("kpkt_2023_SM_KOMITED_DALAM_PERANCANGAN_BANDAR_MALAYSIA_MADANI_KOMUNITI_SEJAHTERA.txt"))
assert "PUTRAJAYA, 9 November 2023" in h23 and "29 penerima Anugerah Penarafan Bandar Pintar 2023" in h23
assert "Senarai penerima dan ringkasan anugerah seperti di Lampiran" in h23 and "SENARAI" not in h23
mpkj = re.sub(r"\s+", " ", text("mpkj_2023-11-09.txt"))
assert "Majlis Perbandaran Kajang (MPKj) pada 9 November 2023 telah menerima Anugerah Penarafan Bandar Pintar" in mpkj
assert "MPKj merupakan di antara 25 Pihak Berkuasa Tempatan (PBT)" in mpkj
mbi = re.sub(r"\s+", " ", text("mbi_2023-11-09.txt"))
assert "9 November 2023-Ipoh antara 5 Bandar Pintar Perintis telah merangkul status Smart City Early Adopter 2023" in mbi
m24 = re.sub(r"\s+", " ", text("kpkt_2024_SM_MAJLIS_BANDAR_PINTAR_NEGARA_MEMPERKASAKAN_AGENDA_EKONOMI_MADANI.txt"))
assert ("Sebanyak 23 PBT yang telah mencapai Tahap 1: Smart City Early Adopter pada tahun 2023 telah secara "
        "sukarela memohon untuk penarafan Tahap 2") in m24
R23 = [("Majlis Perbandaran Kajang", f"council's own news item, {MPKJ} (saved as mpkj_2023-11-09.html)",
        "the council says it was one of 25 councils rated and received a RM200,000 special allocation"),
       ("Majlis Bandaraya Ipoh", f"council's own news item, {MBI} (saved as mbi_2023-11-09.html)",
        "the council says it received a RM 200,000 special allocation grant from KPKT"),
       ("Majlis Bandaraya Johor Bahru", f"inferred from KPKT 24 Oct 2024, {MBPN_2024} and 28 Oct 2024, {HPBS_2024}",
        "rated Tahap 2 in 2024, open only to councils rated Tahap 1 in 2023"),
       ("Perbadanan Putrajaya", f"inferred from KPKT 24 Oct 2024, {MBPN_2024} and 28 Oct 2024, {HPBS_2024}",
        "rated Tahap 2 in 2024, open only to councils rated Tahap 1 in 2023")]
for i, (council, src, why) in enumerate(R23, 1):
    rows.append({
        "economy": "Malaysia", "place_as_printed": council, "place_en": council_en(council), "area_as_printed": "",
        "area_scope": "whole", "project_id": f"MY2023-R-{i:02d}", "programme": RATING,
        "programme_model": "certification", "announcement_date": "2023-11-09", "date_precision": "day",
        "first_treated_year": first_treated("2023-11-09"), "batch": "rating 2023, Tahap 1 Smart City Early Adopter",
        "source": f"{src}; round: KPKT 9 Nov 2023, {HPBS_2023}",
        "note": f"roster: partial (KPKT counts 29 recipients, the Kajang council 25; 4 named); {why}"})

# 3. Rating, 2024 round: the annex of KPKT's 28 October 2024 release lists all 20 councils.
h24 = text("kpkt_2024_SM_HPBS_2024_AGENDA_BANDAR_MAMPAN_DAN_PINTAR.txt")
h24_flat = re.sub(r"\s+", " ", h24)
assert "PUTRAJAYA, 28 Oktober 2024" in h24_flat and "20 penerima Anugerah Penarafan Bandar Pintar 2024" in h24_flat
lists = {}
for level, start, end in [("Tahap 1 Smart City Early Adopter", "“SMART CITY EARLY ADOPTER”", "PENGIKTIRAFAN PENARAFAN"),
                          ("Tahap 2 Developing Smart City", "“DEVELOPING SMART CITY”", "Nota:")]:
    a = h24.index(start) + len(start)
    block = h24[a:h24.index(end, a)]
    lists[level] = [m.group(2).strip() for m in re.finditer(r"^\s*(\d+) (.+?)\s*$", block, re.M)]
    assert [int(m.group(1)) for m in re.finditer(r"^\s*(\d+) ", block, re.M)] == list(range(1, len(lists[level]) + 1))
assert [len(v) for v in lists.values()] == [18, 2]
assert lists["Tahap 2 Developing Smart City"] == ["Majlis Bandaraya Johor Bahru", "Perbadanan Putrajaya"]
k = 0
for level, councils in lists.items():
    for c in councils:
        k += 1
        rows.append({
            "economy": "Malaysia", "place_as_printed": c, "place_en": council_en(c), "area_as_printed": "",
            "area_scope": "whole", "project_id": f"MY2024-R-{k:02d}", "programme": RATING,
            "programme_model": "certification", "announcement_date": "2024-10-28", "date_precision": "day",
            "first_treated_year": first_treated("2024-10-28"), "batch": f"rating 2024, {level}",
            "source": f"KPKT 28 Oct 2024, Lampiran p. 4, {HPBS_2024} (saved as "
                      "kpkt_2024_SM_HPBS_2024_AGENDA_BANDAR_MAMPAN_DAN_PINTAR.pdf)",
            "note": "after the panel; " + ("upgrade of a 2023 Tahap 1 council" if level.startswith("Tahap 2")
                                           else "first rating")})

assert len(rows) == 29 and len({r["project_id"] for r in rows}) == 29
with open(D / "malaysia_kpkt_smart_city.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows:", sum(r["batch"].startswith("MSCF") for r in rows), "pilot cities,",
      sum(r["announcement_date"] == "2023-11-09" for r in rows), "named 2023 ratings,",
      sum(r["announcement_date"] == "2024-10-28" for r in rows), "2024 ratings")
