"""Write korea_molit_smart_city.csv (MOLIT National Pilot Smart Cities 2018, Smart Challenge 2019 to 2021,
and the 2019 theme-type special complex construction programme) from the MOLIT press releases.

argv[1] = designations directory, argv[2] = data/raw/designations/sources.
Every place is checked against the text of the release it is coded from (spaces removed, since the
PDF text layer drops most of them). English names follow Revised Romanization.
"""
import csv, html, re, sys, unicodedata
from collections import Counter
from pathlib import Path
import pypdf

D, C = Path(sys.argv[1]), Path(sys.argv[2])
COLS = ["economy", "place_as_printed", "place_en", "area_as_printed", "area_scope",
        "project_id", "programme", "programme_model", "announcement_date", "date_precision",
        "first_treated_year", "batch", "source", "note"]
KR = "https://www.korea.kr/briefing/pressReleaseView.do?newsId="
DL = "https://www.korea.kr/common/download.do?tblKey=GMN&fileId="
SC = "https://smartcity.go.kr/"


def text(f):
    if f.endswith(".pdf"):
        t = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(C / f).pages)
    else:
        t = (C / f).read_text(encoding="utf-8", errors="replace")
        t = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style).*?</\1>", "", t, flags=re.S)))
    return re.sub(r"\s", "", unicodedata.normalize("NFKC", t))


def first_treated(date):
    y, m = int(date[:4]), int(date[5:7])
    return y if m <= 6 else y + 1


CHALLENGE = "Smart Challenge (스마트 챌린지)"
# batch: (programme, model, announcement date, source file, source text, note shared by the batch)
BATCH = {
    "2018 designation": (
        "National Pilot Smart Cities (국가 시범도시)", "implementation support", "2018-01-29",
        "MOLIT_2018-01-29_national_pilot_cities.pdf",
        f"MOLIT and Fourth Industrial Revolution Committee joint release, {KR}156251178, PDF {DL}191962323, page 3",
        "national pilot city decided at the 4th meeting of the Fourth Industrial Revolution Committee; government "
        "R&D and policy budget concentrated on the site; a new town under construction at designation"),
    "2019 theme complex construction": (
        "Theme-type special complex construction (테마형 특화단지 조성사업)", "implementation support", "2019-02-08",
        "MOLIT_2019-02-08_theme_complex_construction.pdf",
        f"MOLIT release (석간 8 Feb 2019), {KR}156316456, page 1",
        "6 billion won in all to three places; a construction programme before the Smart Challenge, not in design "
        "Table 1, sensitivity check only; project area not coded"),
    "2019 town (master plan support)": (
        CHALLENGE, "implementation support", "2019-03-17",
        "MOLIT_2019-03-17_theme_complex_master_plans.pdf",
        f"MOLIT release (online from 17 Mar 2019 11:00), {KR}156321798, PDF {DL}191903335, page 1",
        "selected for 테마형 특화단지 종합계획 수립 지원 (national grant of 225 million won each); the 2020-02-16 "
        "release counts these four among the 2019 Smart Challenge preliminary projects (타운)"),
    "2019 city (preliminary)": (
        CHALLENGE, "implementation support", "2019-05-02",
        "MOLIT_2019-05-02_city_challenge.pdf",
        f"MOLIT release (online from 2 May 2019 11:00), {KR}156329670, page 1",
        "Smart City Challenge preliminary project, national grant of 1.5 billion won each"),
    "2020 main (from 2019 preliminaries)": (
        CHALLENGE, "implementation support", "2020-02-16",
        "MOLIT_smartcity_2020-02-16_challenge_main.html",
        f"MOLIT smart city portal, {SC}2020/02/16/스마트-시티-타운-챌린지-본사업-대상-총-7개-지역-선정/ "
        "(Wayback Machine copy)",
        "main project (본사업) selected from the 2019 preliminary projects; the place's first selection is its 2019 row"),
    "2020 round": (
        CHALLENGE, "implementation support", "2020-05-28",
        "MOLIT_2020-05-28_smart_challenge_18.pdf",
        f"MOLIT release (online from 28 May 2020 11:00), PDF {DL}191880393, page 1 table",
        "18 projects selected from 80 proposals; city and town are preliminary projects, solution projects are "
        "funded directly"),
    "2021 solution diffusion": (
        CHALLENGE, "implementation support", "2021-03-04",
        "MOLIT_smartcity_2021-03-04_solution_diffusion.html",
        f"MOLIT smart city portal, {SC}2021/03/04/우수-솔루션-확산·규제-없는-실증사업으로-스마트시/ "
        "(Wayback Machine copy), footnote to paragraph 1",
        "스마트챌린지 솔루션 확산사업: proven solutions installed with national funds (60 billion won in all for 23 places)"),
    "2021 main (from 2020 preliminaries)": (
        CHALLENGE, "implementation support", "2021-03-18",
        "MOLIT_2021-03-18_challenge_main_6.pdf",
        f"MOLIT release (online from 18 Mar 2021 11:00), {KR}156441764, PDF {DL}194195708, page 1",
        "main project (본사업) selected from the 11 preliminary projects; the place's first selection is an earlier row"),
    "2021 campus": (
        CHALLENGE, "implementation support", "2021-03-30",
        "MOLIT_2021-03-30_campus_and_town.pdf",
        f"MOLIT release (online from 30 Mar 2021 11:00), {KR}156443652, PDF {DL}194302664, pages 1 to 4",
        "campus challenge: a university-led test of 1.1 to 1.5 billion won; place is the university, area is the test "
        "site printed; sensitivity check only"),
    "2021 town": (
        CHALLENGE, "implementation support", "2021-03-30",
        "MOLIT_2021-03-30_campus_and_town.pdf",
        f"MOLIT release (online from 30 Mar 2021 11:00), {KR}156443652, PDF {DL}194302664, page 1",
        "town challenge, 3 billion won per city (50 percent local)"),
    "2021 city (preliminary)": (
        CHALLENGE, "implementation support", "2021-04-26",
        "MOLIT_smartcity_2021-04-26_city_prelim.html",
        f"MOLIT smart city portal, {SC}2021/04/26/스마트-챌린지-선정-45개-도시-똑똑한-도전-나선다/ "
        "(Wayback Machine copy)",
        "city challenge preliminary project; the release states all 45 Smart Challenge places of 2021 are now selected"),
}

# batch, project_id, place as printed, check string in the source, place_en, area as printed, area_scope, extra note
R = [
    ("2018 designation", "KRNPC2018-1", "세종 5-1 생활권", "세종5-1생활권(83만평)", "Sejong", "5-1생활권(83만평)", "part", ""),
    ("2018 designation", "KRNPC2018-2", "부산 에코델타시티", "부산에코델타시티(세물머리지역중심,66만평)", "Busan",
     "에코델타시티(세물머리지역 중심,66만평)", "part", ""),
    ("2019 theme complex construction", "KRTC2019-1", "대전광역시", "대전광역시", "Daejeon", "", "whole", ""),
    ("2019 theme complex construction", "KRTC2019-2", "경상남도 김해시", "경상남도김해시", "Gimhae, Gyeongsangnam-do", "", "whole", ""),
    ("2019 theme complex construction", "KRTC2019-3", "경기도 부천시", "경기도부천시", "Bucheon, Gyeonggi-do", "", "whole", ""),
    ("2019 town (master plan support)", "KRSC2019-T1", "경남 통영시", "경남통영시", "Tongyeong, Gyeongsangnam-do",
     "재래시장", "part", "; the 2020-02-16 release places it near Dongpirang village (동피랑 마을 인근)"),
    ("2019 town (master plan support)", "KRSC2019-T2", "부산 수영구", "부산수영구", "Suyeong-gu, Busan",
     "남천동 일원, 광안리 해수욕장, 민락동 회센터 주변 (지역 내 3개 관광권역)", "part", ""),
    ("2019 town (master plan support)", "KRSC2019-T3", "서울 성동구", "서울성동구", "Seongdong-gu, Seoul",
     "왕십리 일원", "part", ""),
    ("2019 town (master plan support)", "KRSC2019-T4", "충남 공주시·부여군", "충남공주시·부여군", "Gongju, Chungcheongnam-do",
     "백제역사유적지구 일대(약 1,500,000m2)", "part", "; joint proposal by Gongju and Buyeo, one row each"),
    ("2019 town (master plan support)", "KRSC2019-T4", "충남 공주시·부여군", "충남공주시·부여군", "Buyeo, Chungcheongnam-do",
     "백제역사유적지구 일대(약 1,500,000m2)", "part", "; joint proposal by Gongju and Buyeo, one row each"),
    ("2019 city (preliminary)", "KRSC2019-C1", "광주광역시", "광주광역시", "Gwangju", "충장로 일대", "part", ""),
    ("2019 city (preliminary)", "KRSC2019-C2", "경기도 부천시", "경기도부천시", "Bucheon, Gyeonggi-do", "신흥동 원도심 주거지 일원", "part", ""),
    ("2019 city (preliminary)", "KRSC2019-C3", "수원시", "수원시", "Suwon, Gyeonggi-do", "행궁동", "part", ""),
    ("2019 city (preliminary)", "KRSC2019-C4", "경남 창원시", "경남창원시", "Changwon, Gyeongsangnam-do",
     "진북 일반산업단지와 낙후된 주거지역", "part", ""),
    ("2019 city (preliminary)", "KRSC2019-C5", "대전광역시", "대전광역시", "Daejeon", "중앙시장 일원", "part", ""),
    ("2019 city (preliminary)", "KRSC2019-C6", "인천광역시", "인천광역시", "Incheon", "영종국제도시", "part", ""),
    ("2020 main (from 2019 preliminaries)", "KRSC2020-M1", "경기 부천시", "경기부천시", "Bucheon, Gyeonggi-do", "", "whole", "; city"),
    ("2020 main (from 2019 preliminaries)", "KRSC2020-M2", "대전광역시", "대전광역시", "Daejeon", "", "whole", "; city"),
    ("2020 main (from 2019 preliminaries)", "KRSC2020-M3", "인천광역시", "인천광역시", "Incheon", "", "whole", "; city"),
    ("2020 main (from 2019 preliminaries)", "KRSC2020-M4", "경남 통영시", "경남통영시", "Tongyeong, Gyeongsangnam-do",
     "동피랑 마을 인근", "part", "; town"),
    ("2020 main (from 2019 preliminaries)", "KRSC2020-M5", "서울 성동구", "서울성동구", "Seongdong-gu, Seoul",
     "왕십리 광장을 중심으로", "part", "; town"),
    ("2020 main (from 2019 preliminaries)", "KRSC2020-M6", "부산 수영구", "부산수영구", "Suyeong-gu, Busan",
     "광안리 해수욕장 일대", "part", "; town"),
    ("2020 main (from 2019 preliminaries)", "KRSC2020-M7", "충남 공주‧부여", "충남공주‧부여", "Gongju, Chungcheongnam-do",
     "백제역사유적지구", "part", "; town; joint project, one row each"),
    ("2020 main (from 2019 preliminaries)", "KRSC2020-M7", "충남 공주‧부여", "충남공주‧부여", "Buyeo, Chungcheongnam-do",
     "백제역사유적지구", "part", "; town; joint project, one row each"),
    ("2020 round", "KRSC2020-C1", "강원 강릉", "강원강릉", "Gangneung, Gangwon-do", "", "whole", "; city preliminary"),
    ("2020 round", "KRSC2020-C2", "부산광역시", "부산광역시교통약자", "Busan", "", "whole",
     "; city preliminary; the 2021-03-18 release says the project centred on Dong-gu (동구를 중심으로)"),
    ("2020 round", "KRSC2020-C3", "경남 김해", "경남김해", "Gimhae, Gyeongsangnam-do", "", "whole", "; city preliminary"),
    ("2020 round", "KRSC2020-C4", "제주도", "제주도", "Jeju", "", "prefecture",
     "; city preliminary; Jeju Special Self-Governing Province, two cities"),
    ("2020 round", "KRSC2020-T1", "강원 원주", "강원원주", "Wonju, Gangwon-do", "", "whole", "; town preliminary"),
    ("2020 round", "KRSC2020-T2", "전남 광양", "전남광양", "Gwangyang, Jeollanam-do", "", "whole", "; town preliminary"),
    ("2020 round", "KRSC2020-T3", "경남 창원", "경남창원진해해양공원", "Changwon, Gyeongsangnam-do", "진해해양공원", "part",
     "; town preliminary"),
    ("2020 round", "KRSC2020-T4", "충남 서산", "충남서산산업단지", "Seosan, Chungcheongnam-do", "산업단지", "part",
     "; town preliminary"),
    ("2020 round", "KRSC2020-S01", "강원 양구", "강원양구", "Yanggu, Gangwon-do", "", "whole", "; solution"),
    ("2020 round", "KRSC2020-S02", "충청 서산", "충청서산", "Seosan, Chungcheongnam-do", "도서지역", "part", "; solution"),
    ("2020 round", "KRSC2020-S03", "서울 강동", "서울강동", "Gangdong-gu, Seoul", "", "whole", "; solution"),
    ("2020 round", "KRSC2020-S04", "청주", "청주스마트거리공연", "Cheongju, Chungcheongbuk-do", "", "whole", "; solution"),
    ("2020 round", "KRSC2020-S05", "양천", "양천전기모빌리티", "Yangcheon-gu, Seoul", "", "whole", "; solution"),
    ("2020 round", "KRSC2020-S06", "호남 광산", "호남광산", "Gwangsan-gu, Gwangju", "", "whole", "; solution"),
    ("2020 round", "KRSC2020-S07", "영남 거제", "영남거제포로수용소유적공원", "Geoje, Gyeongsangnam-do",
     "포로수용소 유적공원", "part", "; solution"),
    ("2020 round", "KRSC2020-S08", "순천", "순천전기차", "Suncheon, Jeollanam-do", "", "whole", "; solution"),
    ("2020 round", "KRSC2020-S09", "사천", "사천스쿨존", "Sacheon, Gyeongsangnam-do", "", "whole", "; solution"),
    ("2020 round", "KRSC2020-S10", "완주", "완주스마트버스정류장", "Wanju, Jeollabuk-do", "", "whole", "; solution"),
]
DIFF = [("서울 구로", "Guro-gu, Seoul"), ("서울 동작", "Dongjak-gu, Seoul"), ("서울 중구", "Jung-gu, Seoul"),
        ("부산 남구", "Nam-gu, Busan"), ("대구 달서구", "Dalseo-gu, Daegu"), ("대구 동구", "Dong-gu, Daegu"),
        ("인천 서구", "Seo-gu, Incheon"), ("광주 남구", "Nam-gu, Gwangju"), ("경기 광명", "Gwangmyeong, Gyeonggi-do"),
        ("경기 구리", "Guri, Gyeonggi-do"), ("경기 성남", "Seongnam, Gyeonggi-do"), ("경기 수원", "Suwon, Gyeonggi-do"),
        ("경기 평택", "Pyeongtaek, Gyeonggi-do"), ("강원 춘천", "Chuncheon, Gangwon-do"), ("강원 태백", "Taebaek, Gangwon-do"),
        ("충북 충주", "Chungju, Chungcheongbuk-do"), ("충남 논산", "Nonsan, Chungcheongnam-do"),
        ("충남 홍성", "Hongseong, Chungcheongnam-do"), ("전북 김제", "Gimje, Jeollabuk-do"),
        ("전남 여수", "Yeosu, Jeollanam-do"), ("경북 영주", "Yeongju, Gyeongsangbuk-do"),
        ("경남 밀양", "Miryang, Gyeongsangnam-do"), ("경남 진주", "Jinju, Gyeongsangnam-do")]
# the footnote prints the province once per group ("서울 구로, 동작, 중구/부산 남구/..."); checked as one string
DIFF_LINE = "서울구로,동작,중구/부산남구/대구달서구,동구/인천서구/광주남구/경기광명,구리,성남,수원,평택/강원춘천,태백/충북충주/충남논산,홍성/전북김제/전남여수/경북영주/경남밀양,진주"
for i, (printed, en) in enumerate(DIFF, 1):
    R.append(("2021 solution diffusion", f"KRSC2021-S{i:02d}", printed, DIFF_LINE, en, "", "whole", ""))
R += [
    ("2021 main (from 2020 preliminaries)", "KRSC2021-M1", "부산", "시티챌린지에부산,제주,강릉선정", "Busan",
     "동구를 중심으로", "part", "; city"),
    ("2021 main (from 2020 preliminaries)", "KRSC2021-M2", "제주", "시티챌린지에부산,제주,강릉선정", "Jeju", "", "prefecture",
     "; city; Jeju Special Self-Governing Province, two cities"),
    ("2021 main (from 2020 preliminaries)", "KRSC2021-M3", "강릉", "시티챌린지에부산,제주,강릉선정", "Gangneung, Gangwon-do", "", "whole", "; city"),
    ("2021 main (from 2020 preliminaries)", "KRSC2021-M4", "광양", "타운챌린지에광양,서산,원주선정", "Gwangyang, Jeollanam-do", "", "whole", "; town"),
    ("2021 main (from 2020 preliminaries)", "KRSC2021-M5", "서산", "타운챌린지에광양,서산,원주선정", "Seosan, Chungcheongnam-do", "", "whole", "; town"),
    ("2021 main (from 2020 preliminaries)", "KRSC2021-M6", "원주", "타운챌린지에광양,서산,원주선정", "Wonju, Gangwon-do", "", "whole", "; town"),
    ("2021 campus", "KRSC2021-U1", "한신대학교", "(한신대학교)", "Hanshin University", "부천시", "part", "; test site printed"),
    ("2021 campus", "KRSC2021-U2", "안양대학교", "(안양대학교)", "Anyang University", "안양시", "part", "; test site printed"),
    ("2021 campus", "KRSC2021-U3", "연세대학교", "(연세대학교)", "Yonsei University", "신촌역 상권", "part", "; test site printed"),
    ("2021 campus", "KRSC2021-U4", "한국교통대학교", "(한국교통대학교)", "Korea National University of Transportation",
     "캠퍼스", "part", "; campus not named; the university has more than one campus"),
    ("2021 campus", "KRSC2021-U5", "계명대학교", "(계명대학교)", "Keimyung University", "대구 성서지역과 월배지역", "part",
     "; test site printed"),
    ("2021 campus", "KRSC2021-U6", "성신여자대학교", "(성신여자대학교)", "Sungshin Women's University",
     "서울 성북구 전통시장", "part", "; test site printed"),
    ("2021 campus", "KRSC2021-U7", "동아대학교", "(동아대학교)", "Dong-A University", "공공청사(사하구청)", "part",
     "; test site printed"),
    ("2021 campus", "KRSC2021-U8", "공주대학교", "(공주대학교)", "Kongju National University", "", "part",
     "; test site not named (지방소도시)"),
    ("2021 town", "KRSC2021-T1", "경북 김천시", "경북김천시", "Gimcheon, Gyeongsangbuk-do", "", "whole", ""),
    ("2021 town", "KRSC2021-T2", "경기 과천시", "경기과천시", "Gwacheon, Gyeonggi-do", "", "whole", ""),
    ("2021 town", "KRSC2021-T3", "강원 양양군", "강원양양군", "Yangyang, Gangwon-do", "", "whole", ""),
    ("2021 town", "KRSC2021-T4", "경기 오산시", "경기오산시", "Osan, Gyeonggi-do", "", "whole", ""),
    ("2021 city (preliminary)", "KRSC2021-C1", "대구광역시", "1대구광역시:", "Daegu", "", "whole", ""),
    ("2021 city (preliminary)", "KRSC2021-C2", "강원 춘천", "2강원춘천:", "Chuncheon, Gangwon-do", "", "whole", ""),
    ("2021 city (preliminary)", "KRSC2021-C3", "충청북도", "3충청북도:", "Chungcheongbuk-do", "충북혁신도시, 오송, 오창 지역",
     "prefecture", "; the areas named lie in more than one municipality, resolved when units are linked"),
    ("2021 city (preliminary)", "KRSC2021-C4", "경북 포항", "4경북포항:", "Pohang, Gyeongsangbuk-do", "", "whole", ""),
]

texts = {}
rows = []
for batch, pid, printed, check, en, area, scope, extra in R:
    prog, model, date, f, source, note = BATCH[batch]
    if f not in texts:
        texts[f] = text(f)
    assert re.sub(r"\s", "", check) in texts[f], (pid, check)
    rows.append({"economy": "Korea", "place_as_printed": printed, "place_en": en, "area_as_printed": area,
                 "area_scope": scope, "project_id": pid, "programme": prog, "programme_model": model,
                 "announcement_date": date, "date_precision": "day", "first_treated_year": first_treated(date),
                 "batch": batch, "source": source, "note": note + extra})

# counts printed in the releases
pids = {b: len({r["project_id"] for r in rows if r["batch"] == b}) for b in BATCH}
assert pids["2018 designation"] == 2                                                       # "2곳 선정"
assert pids["2019 town (master plan support)"] + pids["2019 city (preliminary)"] == 10     # "2019년 예비사업 ... 10개 지역"
assert pids["2020 main (from 2019 preliminaries)"] == 7                                    # "총 7개 지역"
assert pids["2020 round"] == 18                                                            # "18개 지역 선정"
assert pids["2021 solution diffusion"] == 23                                               # "전국 23곳"
assert pids["2021 main (from 2020 preliminaries)"] == 6                                    # "6개 지역 선정"
assert pids["2021 campus"] == 8 and pids["2021 town"] == 4                                 # "8개 대학 ... 4개 도시"
assert sum(pids[b] for b in BATCH if b.startswith("2021")) == 45                           # "45곳 모두 선정"
assert pids["2019 theme complex construction"] == 3
assert "45곳모두선정" in texts["MOLIT_smartcity_2021-04-26_city_prelim.html"]
assert pids["2019 town (master plan support)"] + pids["2019 city (preliminary)"] + pids["2020 round"] == 28

with open(D / "korea_molit_smart_city.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows,", len({r["project_id"] for r in rows}), "projects:",
      dict(Counter(r["batch"] for r in rows)))
