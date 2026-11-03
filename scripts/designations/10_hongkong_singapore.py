"""Write hongkong_singapore_smart_city.csv: the whole-city strategies of the two city-states (Singapore Smart Nation,
launched 24 November 2014; Smart City Blueprint for Hong Kong, released 15 December 2017) and the Kowloon East pilot
area (2015 Policy Address, 14 January 2015; sensitivity check only). Each city-state is one unit.

argv[1] = designations directory, argv[2] = data/raw/designations/sources.
Every date and passage is checked against the saved text (hongkong_saved/*.txt and singapore_saved/*.txt, made from the
html saved on 1 Nov 2026); the script stops if one is missing.
"""
import csv, sys
from pathlib import Path

D, C = Path(sys.argv[1]), Path(sys.argv[2])
COLS = ["economy", "place_as_printed", "place_en", "area_as_printed", "area_scope",
        "project_id", "programme", "programme_model", "announcement_date", "date_precision",
        "first_treated_year", "batch", "source", "note"]
SG = "https://www.mddi.gov.sg/newsroom/smart-nation-launch/"
NDR = "https://www.pmo.gov.sg/Photos/national-day-rally-2014?page=1"
BP = "https://www.info.gov.hk/gia/general/201712/15/P2017121400746.htm"
BP_PC = "https://www.info.gov.hk/gia/general/201712/15/P2017121500481.htm"
PA = "https://www.policyaddress.gov.hk/2015/eng/p48.html"
PA_DAY = "https://www.info.gov.hk/gia/general/201501/12/P201501120556.htm"
KE_PE = "https://www.info.gov.hk/gia/general/201611/07/P2016110700326.htm"


def text(folder, name):
    return " ".join((C / folder / name).read_text(encoding="utf-8").split())


def first_treated(date):
    y, m = int(date[:4]), int(date[5:7])
    return y if m <= 6 else y + 1


sg = text("singapore_saved", "mddi_smart-nation-launch.txt")
for s in ["Transcript of Speech By Prime Minister Lee Hsien Loong At Smart Nation Launch 24 Nov 2014",
          "At this year’s National Day Rally, I spoke on how we can use technology to make a difference to our people’s "
          "lives, and to build a Smart Nation.",
          "Therefore our vision is for Singapore to be a Smart Nation",
          "We will set up a Smart Nation Programme Office."]:
    assert s in sg, s
ndr = text("singapore_saved", "pmo_national-day-rally-2014_photos.txt")
assert ("Prime Minister Lee Hsien Loong’s National Day Rally Speech took place on 17 August 2014, at ITE Headquarters & "
        "College Central.") in ndr
bp = text("hongkong_saved", "isd_P2017121400746.txt")
assert ("The Government released today (December 15) the Smart City Blueprint for Hong Kong with a vision to build "
        "Hong Kong into a world-class smart city.") in bp and "Ends/Friday, December 15, 2017" in bp
assert '"Smart Environment"' in bp
pc = text("hongkong_saved", "isd_P2017121500481.txt")
assert "The Smart City Blueprint for Hong Kong released today was endorsed by the Steering Committee at this meeting." in pc
bp2 = text("hongkong_saved", "isd_P2020121000626.txt")
assert "The Government released the Smart City Blueprint for Hong Kong 2.0 (Blueprint 2.0) today (December 10)" in bp2
assert "The Government published in December 2017 the Smart City Blueprint for Hong Kong (Blueprint), setting out 76 initiatives" in bp2
pa = text("hongkong_saved", "policy_address_2015_p48.txt")
assert "50. We intend to use Kowloon East as a pilot area to explore the feasibility of developing a Smart City." in pa
day = text("hongkong_saved", "isd_P201501120556.txt")
assert "will deliver his 2015 Policy Address in the Legislative Council at 11am on Wednesday (January 14)." in day
assert "Ends/Monday, January 12, 2015" in day
ke = text("hongkong_saved", "isd_P2016110700326.txt")
assert ("In the 2015 Policy Address, the Government announced that Kowloon East would be used as a pilot area to explore "
        "the feasibility of developing a smart city.") in ke

rows = [
    {"economy": "Singapore", "place_as_printed": "Singapore", "place_en": "Singapore", "area_as_printed": "",
     "area_scope": "whole", "project_id": "SG2014-SN", "programme": "Smart Nation",
     "programme_model": "whole-city strategy", "announcement_date": "2014-11-24", "date_precision": "day",
     "batch": "Smart Nation launch (24 Nov 2014)",
     "source": f"Prime Minister's speech at the Smart Nation launch, 24 Nov 2014, MDDI transcript, {SG} "
               "(saved as mddi_smart-nation-launch.html)",
     "note": "whole-city strategy of a city-state; first set out at the National Day Rally of 17 Aug 2014 (PMO, "
             f"{NDR}, saved as pmo_national-day-rally-2014_photos.html), which gives the same first treated year; Smart Nation Programme Office announced at the launch; also an ASEAN Smart "
             "Cities Network member from 2018 (ascn.csv)"},
    {"economy": "Hong Kong", "place_as_printed": "Hong Kong", "place_en": "Hong Kong", "area_as_printed": "",
     "area_scope": "whole", "project_id": "HK2017-BP", "programme": "Smart City Blueprint for Hong Kong",
     "programme_model": "whole-city strategy", "announcement_date": "2017-12-15", "date_precision": "day",
     "batch": "Smart City Blueprint (15 Dec 2017)",
     "source": f"ISD press release 15 Dec 2017, {BP} (saved as isd_P2017121400746.htm); opening remarks of the "
               f"Secretary for Innovation and Technology, {BP_PC} (saved as isd_P2017121500481.htm)",
     "note": "whole-city strategy of a city-state, 76 initiatives in six areas including Smart Environment; Blueprint "
             "2.0 (10 Dec 2020) continues it and is not a new designation"},
    {"economy": "Hong Kong", "place_as_printed": "Hong Kong", "place_en": "Hong Kong", "area_as_printed": "Kowloon East",
     "area_scope": "part", "project_id": "HK2015-KE", "programme": "Kowloon East smart city pilot area (2015 Policy Address)",
     "programme_model": "whole-city strategy", "announcement_date": "2015-01-14", "date_precision": "day",
     "batch": "2015 Policy Address (14 Jan 2015)",
     "source": f"2015 Policy Address para. 50, {PA} (saved as policy_address_2015_p48.html), delivered 14 Jan 2015 "
               f"({PA_DAY}, saved as isd_P201501120556.htm); ISD press release 7 Nov 2016, {KE_PE} "
               "(saved as isd_P2016110700326.htm)",
     "note": "sensitivity check only: moves Hong Kong's first treated year to 2015; a pilot area inside one district to "
             "explore feasibility; feasibility study public engagement began 7 Nov 2016"},
]
for r in rows:
    r["first_treated_year"] = first_treated(r["announcement_date"])
assert [r["first_treated_year"] for r in rows] == [2015, 2018, 2015]
assert first_treated("2014-08-17") == 2015  # the National Day Rally date gives the same year
with open(D / "hongkong_singapore_smart_city.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows:", "; ".join(f"{r['project_id']} {r['announcement_date']} -> {r['first_treated_year']}" for r in rows))
