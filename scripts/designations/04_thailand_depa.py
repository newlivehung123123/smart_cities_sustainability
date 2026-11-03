"""Write thailand_depa_smart_city.csv (Thailand smart city logo, ตราสัญลักษณ์เมืองอัจฉริยะ, 2021 to 2025)
from the official award notices posted by depa.

argv[1] = designations directory, argv[2] = data/raw/designations/sources.
The notices are page scans with no text layer, so the project lines below were read from the page
images (1 Nov 2026) and are copied as printed. The counts are checked against the depa page and the
two depa index reports.
"""
import csv, re, sys, unicodedata
from pathlib import Path

D, C = Path(sys.argv[1]), Path(sys.argv[2])
COLS = ["economy", "place_as_printed", "place_en", "area_as_printed", "area_scope",
        "project_id", "programme", "programme_model", "announcement_date", "date_precision",
        "first_treated_year", "batch", "source", "note"]
BASE = "https://depa.or.th/storage/app/media/SmartCity/Tab_SmartCity/"
PAGE = "https://depa.or.th/th/smart-city-plan/existing-smart-city"

PROV = {"ขอนแก่น": "Khon Kaen", "ภูเก็ต": "Phuket", "ลำปาง": "Lampang", "ระยอง": "Rayong",
        "กรุงเทพมหานคร": "Bangkok", "เชียงใหม่": "Chiang Mai", "ตรัง": "Trang", "ยะลา": "Yala",
        "ฉะเชิงเทรา": "Chachoengsao", "ชลบุรี": "Chon Buri", "นครสวรรค์": "Nakhon Sawan",
        "พิษณุโลก": "Phitsanulok", "เชียงราย": "Chiang Rai", "น่าน": "Nan", "นครราชสีมา": "Nakhon Ratchasima",
        "อุบลราชธานี": "Ubon Ratchathani", "กระบี่": "Krabi", "พังงา": "Phang Nga", "สตูล": "Satun",
        "สุราษฎร์ธานี": "Surat Thani", "สงขลา": "Songkhla", "ปัตตานี": "Pattani", "นราธิวาส": "Narathiwat",
        "สมุทรปราการ": "Samut Prakan", "นครศรีธรรมราช": "Nakhon Si Thammarat"}
LOCAL = {"เทศบาลนคร": "city municipality", "เทศบาลเมือง": "town municipality",
         "เทศบาลตำบล": "subdistrict municipality", "องค์การบริหารส่วนตำบล": "subdistrict administrative organisation"}
LOCAL_EN = {"เชียงใหม่": "Chiang Mai", "ยะลา": "Yala", "แสนสุข": "Saen Suk", "ระยอง": "Rayong",
            "เขาคันทรง": "Khao Khan Song", "พิษณุโลก": "Phitsanulok", "เชียงราย": "Chiang Rai", "น่าน": "Nan",
            "เกาะสมุย": "Ko Samui", "หาดใหญ่": "Hat Yai", "ปัตตานี": "Pattani", "นราธิวาส": "Narathiwat",
            "เทพราช": "Thepparat", "นิคมพัฒนา": "Nikhom Phatthana", "บวกค้าง": "Buak Khang",
            "นครศรีธรรมราช": "Nakhon Si Thammarat"}

# Notice: number, signed, decision body and meeting, file saved in sources, URL, project lines as printed
NOTICES = [
    ("subcommittee notice 1/2564", "2021-08-13", "Subcommittee meeting 1/2564 of 6 May 2021 approved the list",
     "depa_notice_subcommittee_1-2564.pdf", BASE + "Announcement1_64.pdf", [
        "โครงการแผนพัฒนาขอนแก่นเมืองอัจฉริยะ จังหวัดขอนแก่น",
        "โครงการแผนพัฒนาภูเก็ตเมืองอัจฉริยะ จังหวัดภูเก็ต",
        "โครงการแผนพัฒนาแม่เมาะเมืองน่าอยู่ จังหวัดลำปาง",
        "โครงการแผนพัฒนาเมืองอัจฉริยะวังจันทร์วัลเลย์ จังหวัดระยอง",
        "โครงการแผนพัฒนาสามย่านสมาร์ทซิตี้ กรุงเทพมหานคร"]),
    ("subcommittee notice 2/2564", "2021-10-28", "Subcommittee meeting 2/2564 of 23 September 2021 approved the list",
     "depa_notice_subcommittee_2-2564.pdf", BASE + "Announcement2_64.pdf", [
        "โครงการแผนพัฒนาเมืองอัจฉริยะย่านพระราม 4 กรุงเทพมหานคร",
        "โครงการแผนพัฒนาเมืองอัจฉริยะเพื่อสนับสนุนการพัฒนาพื้นที่โดยรอบคลองผดุงกรุงเกษม กรุงเทพมหานคร",
        "โครงการแผนพัฒนาเมืองอัจฉริยะมักกะสันเพื่อสนับสนุนบริการรถไฟของโครงการรถไฟความเร็วสูงเชื่อมสามสนามบิน กรุงเทพมหานคร",
        "โครงการแผนพัฒนาการพัฒนาเมืองเก่าอย่างชาญฉลาด เทศบาลนครเชียงใหม่ จังหวัดเชียงใหม่",
        "โครงการแผนพัฒนามหาวิทยาลัยเชียงใหม่เมืองอัจฉริยะ ความเป็นเลิศที่ยั่งยืนสู่ชุมชน จังหวัดเชียงใหม่",
        "โครงการแผนพัฒนาเมืองศรีตรัง (Sri-Trang City) จังหวัดตรัง",
        "โครงการแผนพัฒนายะลาเมืองอัจฉริยะเพื่อการมีส่วนร่วมของประชาชน เทศบาลนครยะลา จังหวัดยะลา",
        "โครงการแผนพัฒนาฉะเชิงเทรา เมืองน่าอยู่ น่าเที่ยว น่าลงทุน จังหวัดฉะเชิงเทรา",
        "โครงการแผนพัฒนาแสนสุขสมาร์ทซิตี้ เทศบาลเมืองแสนสุข จังหวัดชลบุรี",
        "โครงการแผนพัฒนานครสวรรค์สมาร์ทซิตี้ จังหวัดนครสวรรค์"]),
    ("subcommittee notice 1/2565", "2022-08-27", "Subcommittee meeting 1/2565 of 5 August 2022 approved the list",
     "depa_notice_subcommittee_1-2565.pdf", BASE + "Announcement1_65.pdf", [
        "โครงการนครระยอง : เมืองอัจฉริยะและน่าอยู่ เทศบาลนครระยอง จังหวัดระยอง",
        "โครงการเขาคันทรงโมเดล เมืองแห่งความสุขที่พึงประสงค์และสังคมแห่งการแบ่งปัน องค์การบริหารส่วนตำบลเขาคันทรง อำเภอศรีราชา จังหวัดชลบุรี",
        "โครงการเมืองอัจฉริยะจังหวัดพิษณุโลก จังหวัดพิษณุโลก",
        "โครงการพิษณุโลกนครอัจฉริยะอย่างยั่งยืน เทศบาลนครพิษณุโลก จังหวัดพิษณุโลก",
        "โครงการนครเชียงรายสู่เมืองอัจฉริยะ เทศบาลนครเชียงราย จังหวัดเชียงราย",
        "โครงการเมืองน่านสู่เมืองอัจฉริยะ เทศบาลเมืองน่าน จังหวัดน่าน",
        "โครงการโคราชเมืองอัจฉริยะ (Korat Smart City) จังหวัดนครราชสีมา",
        "โครงการสมาร์ทซิตี้อุบลราชธานี จังหวัดอุบลราชธานี",
        "โครงการกระบี่เมืองอัจฉริยะ จังหวัดกระบี่",
        "โครงการจังหวัดพังงาสู่เมืองอัจฉริยะ จังหวัดพังงา",
        "โครงการสตูลสมาร์ทซิตี้ จังหวัดสตูล",
        "โครงการพัฒนาเทศบาลนครเกาะสมุย สู่เมืองอัจฉริยะอย่างยั่งยืน เทศบาลนครเกาะสมุย จังหวัดสุราษฎร์ธานี",
        "โครงการหาดใหญ่เมืองอัจฉริยะสีเขียว เทศบาลนครหาดใหญ่ จังหวัดสงขลา",
        "โครงการปัตตานีเมืองอัจฉริยะ เทศบาลเมืองปัตตานี จังหวัดปัตตานี",
        "โครงการเมืองสิ่งแวดล้อมสร้างสรรค์นราธิวาส เทศบาลเมืองนราธิวาส จังหวัดนราธิวาส"]),
    ("subcommittee notice 1/2566", "2023-08-17", "Subcommittee meeting 1/2566 of 26 July 2023 approved the list",
     "depa_notice_subcommittee_1-2566.pdf", BASE + "2023-Sep-update/66-1_announcement.pdf", [
        "โครงการลำปางเมืองอัจฉริยะ จังหวัดลำปาง",
        "โครงการสมุทรปราการสมาร์ทซิตี้ จังหวัดสมุทรปราการ",
        "โครงการเทพราชเมืองอัจฉริยะ เทศบาลตำบลเทพราช จังหวัดฉะเชิงเทรา",
        "โครงการนิคมพัฒนาเมืองอัจฉริยะ เทศบาลตำบลนิคมพัฒนา จังหวัดระยอง",
        "โครงการเมืองไตยองบวกค้างสมาร์ตซิตี้ เทศบาลตำบลบวกค้าง จังหวัดเชียงใหม่",
        "โครงการเทศบาลนครนครศรีธรรมราชเมืองอัจฉริยะ เทศบาลนครนครศรีธรรมราช จังหวัดนครศรีธรรมราช"]),
    ("National Digital Economy and Society Committee notice of 4 September 2025", "2025-09-04",
     "Committee meeting 2/2568 of 19 August 2025, following the promotion committee meeting 2/2568 of 1 August 2025; "
     "logo valid from 1 August 2025",
     "depa_notice_NDESC_award_2568.pdf", BASE + "2025-sep-update/68-smartcitygrant.pdf", [
        "โครงการภูเก็ตทินิคอนวัลเลย์ จังหวัดภูเก็ต"]),
]
# Named parts smaller than the place printed (area_scope part): substring of the project line -> area as printed
PART = {"แม่เมาะ": "แม่เมาะ", "วังจันทร์วัลเลย์": "วังจันทร์วัลเลย์", "สามย่าน": "สามย่าน",
        "พระราม 4": "ย่านพระราม 4", "คลองผดุงกรุงเกษม": "พื้นที่โดยรอบคลองผดุงกรุงเกษม", "มักกะสัน": "มักกะสัน",
        "เมืองเก่า": "เมืองเก่า", "มหาวิทยาลัยเชียงใหม่": "มหาวิทยาลัยเชียงใหม่", "ทินิคอนวัลเลย์": "ทินิคอนวัลเลย์"}
# Projects renewed for two years from 1 August 2025 (renewal notice, items 1 to 16), keyed by a substring of the project line
RENEWED = ["แม่เมาะ", "คลองผดุงกรุงเกษม", "ยะลาเมืองอัจฉริยะ", "สามย่าน", "ขอนแก่นเมืองอัจฉริยะ", "วังจันทร์วัลเลย์",
           "นครเชียงราย", "ภูเก็ตเมืองอัจฉริยะ", "มหาวิทยาลัยเชียงใหม่", "เมืองศรีตรัง", "โคราช", "แสนสุข", "เมืองน่าน",
           "เมืองเก่า", "กระบี่", "ฉะเชิงเทรา เมืองน่าอยู่"]
LABEL = ("logo (ตราสัญลักษณ์) certifying the place as a smart city development area, valid two years; "
         "the notice names no funding")


def first_treated(date):
    y, m = int(date[:4]), int(date[5:7])
    return y if m <= 6 else y + 1


def place(line):
    """Place printed after the project name: a local government (เทศบาล or อบต.) if named, else the province."""
    prov = "กรุงเทพมหานคร" if line.endswith("กรุงเทพมหานคร") else re.search(r"จังหวัด(\S+)$", line).group(1)
    m = re.search(r"(เทศบาลนคร|เทศบาลเมือง|เทศบาลตำบล|องค์การบริหารส่วนตำบล)(\S+)( อำเภอ\S+)? (จังหวัด\S+)$", line)
    if m:
        printed = line[m.start():]
        en = f"{LOCAL_EN[m.group(2)]} {LOCAL[m.group(1)]}"
        if m.group(3):
            en += ", Si Racha district"
        return prov, printed, f"{en}, {PROV[prov]}", True
    printed = "กรุงเทพมหานคร" if prov == "กรุงเทพมหานคร" else f"จังหวัด{prov}"
    return prov, printed, PROV[prov] if prov == "กรุงเทพมหานคร" else f"{PROV[prov]} Province", False


rows, renewed = [], set()
for k, (notice, date, body, file, url, lines) in enumerate(NOTICES, 1):
    for i, line in enumerate(lines, 1):
        line = unicodedata.normalize("NFC", line)
        prov, printed, en, local = place(line)
        part = next((v for s, v in PART.items() if s in line), "")
        scope = "part" if part else ("whole" if local or prov == "กรุงเทพมหานคร" else "prefecture")
        ren = next((s for s in RENEWED if s in line), None)
        if ren:
            renewed.add(ren)
        rows.append({
            "economy": "Thailand", "place_as_printed": printed, "place_en": en,
            "area_as_printed": part, "area_scope": scope, "project_id": f"TH{date[:4]}-{k}-{i:02d}",
            "programme": "Smart city logo (depa, Smart City Development Committee)", "programme_model": "certification",
            "announcement_date": date, "date_precision": "day", "first_treated_year": first_treated(date),
            "batch": notice, "source": f"{notice}, {url}, item {i} (saved as {file}); list page {PAGE}",
            "note": f"project as printed: {line}; {LABEL}; {body}"
                    + ("; renewed for two years from 1 August 2025 (renewal notice of 4 September 2025)" if ren else "")
                    + ("; after the panel" if date >= "2025" else "")})

# Checks against the depa page (37 cities as of August 2025) and the batch counts it prints
html = (C / "depa_existing-smart-city_2026-11-01.html").read_text(encoding="utf-8")
assert "จำนวน 37 เมือง (ข้อมูล ณ ส.ค. 68)" in re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
assert len(rows) == 37 and [len(n[5]) for n in NOTICES] == [5, 10, 15, 6, 1]
assert renewed == set(RENEWED)                     # all 16 renewal items found
provs = lambda n: len({place(l)[0] for x in NOTICES[:n] for l in x[5]})
assert provs(3) == 23 and provs(4) == 25           # TSCCI 2023: 30 cities in 23 provinces; 36 cities in 25 provinces
with open(D / "thailand_depa_smart_city.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows;", sum(r["area_scope"] == "part" for r in rows), "part,",
      sum(r["area_scope"] == "prefecture" for r in rows), "province only")
