"""Write macau_smart_city.csv: Macao's smart city framework agreement with Alibaba Group (signed 4 August 2017), coded as
a whole-city strategy. Macao is one unit; it is not estimated and is kept out of the Singapore and Hong Kong donor pools.
Also checks the passages quoted for Mongolia, Laos and Myanmar, which have no national designation list beyond the ASEAN
Smart Cities Network members in ascn.csv (see Others_sources_read_2026-11-01.txt). No rows are written for them.

argv[1] = designations directory, argv[2] = data/raw/designations/sources.
Every date and passage is checked against the saved text (macau_saved/*.txt and others_saved/*.txt, made from the html or
PDF saved on 1 Nov 2026); the script stops if one is missing.
"""
import csv, sys
from pathlib import Path

D, C = Path(sys.argv[1]), Path(sys.argv[2])
COLS = ["economy", "place_as_printed", "place_en", "area_as_printed", "area_scope",
        "project_id", "programme", "programme_model", "announcement_date", "date_precision",
        "first_treated_year", "batch", "source", "note"]
GCS = "https://www.gcs.gov.mo/news/detail/en/N17HN4XH2R"


def text(folder, name):
    return " ".join((C / folder / name).read_text(encoding="utf-8").split())


def first_treated(date):
    y, m = int(date[:4]), int(date[5:7])
    return y if m <= 6 else y + 1


mo = text("macau_saved", "gcs.gov.mo_news_detail_en_N17HN4XH2R.txt")
for s in ["Developing Macao as a smart city to optimise services to the public Office of the Government Spokesperson "
          "2017-08-14",
          "The Government and Alibaba Group signed on 4 August a “Framework Agreement of Strategic Cooperation on Smart City "
          "Development”, encompassing a series of projects to upgrade Macao’s development in the fields of cloud computing "
          "and big data technology, spanning from 2017 to 2021",
          "Building Macao as a smart city is a Government policy outlined in the city’s Five-Year Development Plan.",
          "First phase (August 2017 to June 2019)",
          "Second phase (July 2019 to June 2021) Building a cloud computing centre and a big data mapping platform (second "
          "phase) Environmental protection"]:
    assert s in mo, s

# Mongolia, Laos and Myanmar: passages quoted in the sources file; nothing is coded from them.
mn = text("others_saved", "mongolia_un_mayors_office.txt")
assert "Master Plan is approved and being implemented in order to make green and smart city." in mn
la = text("others_saved", "laos_odm_smart-city-project-tops-agenda.txt")
assert ("A plan to create “smart” and “eco” cities in Luang Namtha, and Oudomxay provinces topped the agenda at the "
        "government’s monthly meeting for October.") in la
assert "2019-10-31" in (C / "others_saved" / "laos_odm_smart-city-project-tops-agenda.html").read_text(encoding="utf-8")
mm = text("others_saved", "myanmar_eleven_150732.txt")
assert "Published 23 December 2019" in mm
assert ("Ministry of Construction starts implementing the smart city projects in Nay Pyi Taw, Yangon and Mandalay, said "
        "Union Minister for Construction U Han Zaw.") in mm

row = {"economy": "Macau", "place_as_printed": "Macao", "place_en": "Macau", "area_as_printed": "", "area_scope": "whole",
       "project_id": "MO2017-AL", "programme": "Smart city development (framework agreement with Alibaba Group)",
       "programme_model": "whole-city strategy", "announcement_date": "2017-08-04", "date_precision": "day",
       "batch": "Framework Agreement of Strategic Cooperation on Smart City Development (4 Aug 2017)",
       "source": f"Government Information Bureau release 14 Aug 2017, {GCS} (saved as "
                 "gcs.gov.mo_news_detail_en_N17HN4XH2R.html)",
       "note": "whole-city strategy of a one-unit economy, projects 2017 to 2021 in two phases, environmental protection in "
               "the second phase (July 2019 to June 2021); Macau is not estimated and is excluded from the Singapore and "
               "Hong Kong donor pools"}
row["first_treated_year"] = first_treated(row["announcement_date"])
assert row["first_treated_year"] == 2018
with open(D / "macau_smart_city.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    w.writerow(row)
print("1 row:", row["project_id"], row["announcement_date"], "->", row["first_treated_year"],
      "; Mongolia, Laos and Myanmar passages checked, no rows")
