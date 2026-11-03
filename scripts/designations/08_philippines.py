"""Write philippines_dict_digital_cities.csv: the 25 locations of Digital Cities 2025 (DICT, IBPAP and Leechiu
Property Consultants, launched 30 June 2020), one row per city or municipality, so the three clusters give 31 rows.

argv[1] = designations directory, argv[2] = data/raw/designations/sources.
The list is read three times from the saved text (philippines_saved/*.txt, made from the html or PDF saved on
1 Nov 2026): the Philippine News Agency report, the GMA News report and the table of contents of the DICT primer.
The script stops if the three lists, or the cluster members, differ.
Digital Cities 2025 is an IT-BPM hub programme, not a smart city programme; the rows are for a sensitivity check only.
"""
import csv, re, sys
from pathlib import Path

D, C = Path(sys.argv[1]), Path(sys.argv[2])
S = C / "philippines_saved"
COLS = ["economy", "place_as_printed", "place_en", "area_as_printed", "area_scope",
        "project_id", "programme", "programme_model", "announcement_date", "date_precision",
        "first_treated_year", "batch", "source", "note"]
PNA = "https://www.pna.gov.ph/articles/1107517"
GMA = "https://www.gmanetwork.com/news/scitech/technology/744836/dict-ibpap-leechiu-pick-25-cities-as-next-it-bpm-hubs/story/"
PRIMER = "https://dict.gov.ph/wp-content/uploads/2021/11/Digital-Cities-2025-Primer.pdf"
DICT_PAGE = "https://dict.gov.ph/digital-cities-2025/"
PROGRAMME = "Digital Cities 2025 (DICT, IBPAP, LPC)"
DATE = "2020-06-30"
# City roadmaps linked on the DICT programme page (Wayback capture of 3 Dec 2021), by the name used in the list.
ROADMAP = {"General Santos City", "Batangas City", "Zamboanga City", "Tuguegarao City", "Taytay",
           "Puerto Princesa City", "Legazpi City"}


def text(name):
    return re.sub(r"[ \t]+", " ", (S / name).read_text(encoding="utf-8"))


def first_treated(date):
    y, m = int(date[:4]), int(date[5:7])
    return y if m <= 6 else y + 1


def key(s):
    """Tokens of a place name without 'City', 'and' or punctuation, so the three printings can be compared."""
    return re.sub(r"\b(city|and)\b|[^a-zñ ]", " ", s.lower()).split()


def members(s):
    return [m.strip() for m in re.split(r",\s*(?:and\s+)?|\s+and\s+", s) if m.strip()]


# 1. GMA News prints the 25 one per line, clusters with their members in brackets.
gma = text("gma_744836.txt")
assert "Published June 30, 2020 4:49pm" in gma
a = gma.index("The selected cities are the following:\n") + len("The selected cities are the following:\n")
listed = gma[a:gma.index("\nUnder the initiative", a)].strip().split("\n")
listed = [x.strip() for x in listed]
assert len(listed) == 25 and listed[0] == "Balanga City" and listed[-1] == "Zamboanga City"
assert ("The Centers of Excellence refer to cities that are already established IT-BPM hubs such as Metro Manila, "
        "Metro Cebu, Metro Clark, Bacolod City, Davao City, and Iloilo City.") in gma

# 2. The Philippine News Agency (Wayback copy of 10 July 2020) prints the same 25 in one sentence.
pna = text("pna_1107517_wayback_20200710.txt")
assert "June 30, 2020, 8:17 pm" in pna
a = pna.index("identified the 25 cities as ") + len("identified the 25 cities as ")
sentence = pna[a:pna.index(".\n", a)]
assert key(sentence) == key(" ".join(listed)), "PNA and GMA lists differ"
for s in ["will receive tailor-fit interventions aside from institutional, development, and infrastructure "
          "developments, marketing, and promotion",
          "Administrative Order No. 18, series of 2019",
          "Caintic said the 25 cities will receive “targeted efforts” including improving connectivity"]:
    assert s in pna, s

# 3. The DICT primer lists the same 25 location profiles and prints the cluster members in each profile heading.
pr = text("DICT_Digital-Cities-2025-Primer_wayback_20220626.txt")
a = pr.index("Location Profiles")
toc = [m.group(1).strip() for m in re.finditer(r"^(.+?) ?[….]{3,}\s*\d+\s*$", pr[a:pr.index("Phase 2 Interventions", a)], re.M)]
assert toc == [re.sub(r" \(.*\)$", "", x) for x in listed], "primer and GMA lists differ"
flat = re.sub(r"\s+", " ", pr)
assert ("Aside from the identification of the 25 Digital Cities for 2025, DICT, in collaboration with IBPAP, also aims "
        "to provide the necessary support in 4 areas: institutional development, talent attraction and development, "
        "infrastructure development, and marketing and promotion.") in flat
assert "This 2020, DICT, IBPAP, and LPC launched Digital Cities 2025" in flat
profile = {}
for cl in ["Laguna Cluster", "Metro Cavite", "Metro Rizal"]:
    m = re.search(r"^" + cl + r" *\n\((.+?)\) *\n(?:Luzon|Visayas|Mindanao)", pr, re.M)
    profile[cl] = members(m.group(1))

rows = []
for i, item in enumerate(listed, 1):
    m = re.fullmatch(r"(.+?) \((.+)\)", item)
    if m:
        cl, gma_members = m.group(1), members(m.group(2))
        pairs = []
        for g in gma_members:
            hit = [p for p in profile[cl] if key(p) == key(g)]
            assert len(hit) == 1, (cl, g)
            pairs.append((g, hit[0]))
        assert len(pairs) == len(profile[cl])
    else:
        cl, pairs = "", [(item, item)]
    for printed, en in pairs:
        note = ["sensitivity check only: an IT-BPM hub programme, not a smart city programme",
                "DICT and IBPAP support in institutional development, talent, infrastructure and marketing "
                "(primer pp. 59-60); no transfer to the city is stated"]
        if en in ROADMAP or printed in ROADMAP:
            note.append("city roadmap listed on the DICT programme page (captured 3 Dec 2021)")
        if cl:
            note.append(f"one of {len(pairs)} local government units of the {cl if cl.endswith('Cluster') else cl + ' cluster'}, which share one project_id")
        rows.append({
            "economy": "Philippines", "place_as_printed": printed, "place_en": en,
            "area_as_printed": item if cl else "", "area_scope": "whole", "project_id": f"PH2020-DC-{i:02d}",
            "programme": PROGRAMME, "programme_model": "implementation support", "announcement_date": DATE,
            "date_precision": "day", "first_treated_year": first_treated(DATE),
            "batch": "Digital Cities 2025 (25 locations, 2020)",
            "source": f"PNA 30 Jun 2020, {PNA} (Wayback 10 Jul 2020, saved as pna_1107517_wayback_20200710.html); "
                      f"GMA News 30 Jun 2020, {GMA} (saved as gma_744836.html); DICT primer, {PRIMER} "
                      f"(Wayback 26 Jun 2022, saved as DICT_Digital-Cities-2025-Primer_wayback_20220626.pdf)",
            "note": "; ".join(note)})

assert len(rows) == 31 and len({r["project_id"] for r in rows}) == 25
assert sum("roadmap" in r["note"] for r in rows) == 7
with open(D / "philippines_dict_digital_cities.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows,", len({r["project_id"] for r in rows}), "locations,",
      sum(bool(r["area_as_printed"]) for r in rows), "cluster rows")
