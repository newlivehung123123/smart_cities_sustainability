"""Write indonesia_kominfo_smart_city.csv (Gerakan Menuju (100) Smart City, Kominfo Ditjen Aptika: the rounds of 2017,
2018, 2019, 2021, 2022, 2023 and 2024) from the ministry's releases and the MoU and award lists printed in the press.

argv[1] = designations directory, argv[2] = data/raw/designations/sources.
Every roster is parsed from the saved text of its source and must match the province table below exactly, so a place
that is missing, added or misspelled stops the script. Komdigi passages come from komdigi_api_extract_2026-11-01.txt
(read in a browser); the other pages are in indonesia_saved/ as html with a txt copy made by totxt_helper.py.
Kota and kabupaten are both second-level units (ADM2), so area_scope is whole for every row. Provinces were added by
hand, as at the announcement date, and are checked against the boundary file when units are linked.
"""
import csv, re, sys, unicodedata
from collections import Counter
from pathlib import Path

D, C = Path(sys.argv[1]), Path(sys.argv[2]) / "indonesia_saved"
COLS = ["economy", "place_as_printed", "place_en", "area_as_printed", "area_scope",
        "project_id", "programme", "programme_model", "announcement_date", "date_precision",
        "first_treated_year", "batch", "source", "note"]
KD = "https://www.komdigi.go.id/berita/"
PROG = "Gerakan Menuju (100) Smart City (Kominfo Ditjen Aptika)"
MODEL = "implementation support"
SHARED = "master plan guidance (bimbingan) under an MoU with Ditjen Aptika; no direct funding found"


def text(f):
    t = unicodedata.normalize("NFKC", (C / f).read_text(encoding="utf-8", errors="replace"))
    return "\n".join(re.sub(r"[ \t]+", " ", x).strip() for x in t.splitlines())


def block(path):
    t = text("komdigi_api_extract_2026-11-01.txt")
    i = t.index("### " + path + "\n")
    j = t.find("\n### ", i + 1)
    return t[i:] if j < 0 else t[i:j]


def first_treated(date):
    y, m = int(date[:4]), int(date[5:7])
    return y if m <= 6 else y + 1


def split_list(s):
    return [x.strip() for x in re.split(r",\s*(?:dan\s+)?|\s+dan\s+", s) if x.strip()]


def numbered(t, n):
    items = re.findall(r"(?m)^(\d+)\. (.+?)$", t)
    assert [int(k) for k, _ in items] == list(range(1, n + 1)), items[:3]
    return [v for _, v in items]


# printed spelling -> canonical name; every correction is noted on its row
SPELL = {"Kota Probolinggi": "Kota Probolinggo", "Kota Pelembang": "Kota Palembang",
         "Kabupaten Musin Banyuasing": "Kab Musi Banyuasin", "Kota Mataran": "Kota Mataram",
         "Kota Pelalawan": "Kab Pelalawan", "Kabupatet Banyuasin": "Kab Banyuasin",
         "Kota Kabupaten Mimika": "Kab Mimika", "Kabupaten Lombok timur": "Kab Lombok Timur",
         "Payakumbuh": "Kota Payakumbuh", "Bone Bolanga": "Kab Bone Bolango"}


def canon(printed, prefix=""):
    if printed in SPELL:
        return SPELL[printed]
    return re.sub(r"^Kabupaten ", "Kab ", prefix + printed)


PROV = {
    "Aceh": ["Kota Banda Aceh", "Kota Sabang", "Kab Aceh Jaya"],
    "North Sumatra": ["Kota Medan", "Kota Binjai", "Kab Langkat", "Kab Deli Serdang", "Kota Sibolga", "Kab Dairi",
                      "Kab Humbang Hasundutan", "Kab Karo", "Kab Pakpak Bharat", "Kab Samosir", "Kab Simalungun",
                      "Kab Tapanuli Utara", "Kab Toba Samosir", "Kota Tebing Tinggi", "Kab Tapanuli Selatan",
                      "Kota Tanjungbalai", "Kota Pematangsiantar", "Kab Asahan", "Kab Tapanuli Tengah"],
    "West Sumatra": ["Kota Padang", "Kab Solok", "Kota Padang Panjang", "Kab Padang Pariaman", "Kab Lima Puluh Kota",
                     "Kota Payakumbuh", "Kota Bukittinggi", "Kota Pariaman", "Kab Agam", "Kota Sawahlunto",
                     "Kab Solok Selatan", "Kota Solok"],
    "Riau": ["Kab Siak", "Kab Pelalawan", "Kota Pekanbaru", "Kota Dumai", "Kab Indragiri Hilir"],
    "Riau Islands": ["Kota Tanjung Pinang", "Kota Batam"],
    "Jambi": ["Kota Jambi", "Kab Sarolangun", "Kab Batanghari", "Kab Muaro Jambi"],
    "Bengkulu": ["Kab Bengkulu Utara", "Kota Bengkulu"],
    "South Sumatra": ["Kab Banyuasin", "Kota Palembang", "Kab Muara Enim", "Kab Musi Banyuasin", "Kab Musi Rawas",
                      "Kab Ogan Komering Ilir", "Kab Ogan Komering Ulu"],
    "Bangka Belitung Islands": ["Kab Belitung", "Kab Belitung Timur", "Kab Bangka Selatan", "Kota Pangkalpinang",
                                "Kab Bangka"],
    "Lampung": ["Kota Bandar Lampung", "Kab Lampung Tengah", "Kota Metro"],
    "Banten": ["Kota Tangerang", "Kota Tangerang Selatan", "Kota Cilegon", "Kab Tangerang", "Kota Serang", "Kab Lebak",
               "Kab Serang"],
    "West Java": ["Kota Bogor", "Kota Bandung", "Kota Cirebon", "Kota Bekasi", "Kota Sukabumi", "Kab Purwakarta",
                  "Kota Cimahi", "Kab Bogor", "Kota Depok", "Kab Bandung", "Kab Indramayu", "Kab Cirebon", "Kab Bekasi",
                  "Kab Karawang", "Kab Subang", "Kab Sukabumi", "Kab Sumedang", "Kota Tasikmalaya", "Kab Majalengka",
                  "Kab Kuningan", "Kab Bandung Barat", "Kab Garut", "Kab Tasikmalaya", "Kab Ciamis", "Kota Banjar"],
    "Central Java": ["Kota Semarang", "Kab Sukoharjo", "Kab Boyolali", "Kab Banyumas", "Kota Surakarta",
                     "Kab Magelang", "Kab Batang", "Kab Kudus", "Kab Pati", "Kab Jepara", "Kab Kendal", "Kab Blora",
                     "Kab Pemalang", "Kab Grobogan", "Kota Pekalongan", "Kota Magelang", "Kab Klaten", "Kab Sragen",
                     "Kab Demak", "Kab Kebumen", "Kab Wonosobo", "Kab Karanganyar", "Kab Purworejo", "Kab Semarang",
                     "Kab Temanggung", "Kab Wonogiri", "Kab Brebes", "Kota Tegal", "Kab Rembang", "Kab Cilacap",
                     "Kab Banjarnegara", "Kab Tegal", "Kab Pekalongan", "Kab Purbalingga"],
    "Special Region of Yogyakarta": ["Kab Sleman", "Kab Bantul", "Kab Kulon Progo", "Kota Yogyakarta",
                                     "Kab Gunung Kidul"],
    "East Java": ["Kab Gresik", "Kab Sidoarjo", "Kab Bojonegoro", "Kab Banyuwangi", "Kota Surabaya", "Kab Sumenep",
                  "Kota Probolinggo", "Kab Lamongan", "Kab Jember", "Kab Blitar", "Kab Tuban", "Kab Pasuruan",
                  "Kota Batu", "Kota Kediri", "Kota Madiun", "Kab Situbondo", "Kab Malang", "Kab Pacitan",
                  "Kab Probolinggo", "Kota Malang", "Kota Pasuruan", "Kab Magetan", "Kab Ngawi", "Kab Ponorogo",
                  "Kab Trenggalek", "Kab Nganjuk", "Kab Jombang", "Kab Mojokerto", "Kota Mojokerto", "Kab Kediri",
                  "Kota Blitar", "Kab Lumajang", "Kab Bondowoso", "Kab Sampang", "Kab Pamekasan"],
    "Bali": ["Kab Badung", "Kota Denpasar", "Kab Jembrana", "Kab Tabanan", "Kab Klungkung", "Kab Buleleng",
             "Kab Karangasem", "Kab Bangli", "Kab Gianyar"],
    "West Nusa Tenggara": ["Kab Lombok Timur", "Kab Sumbawa", "Kota Mataram", "Kab Lombok Barat", "Kab Lombok Tengah",
                           "Kab Lombok Utara", "Kab Sumbawa Barat"],
    "East Nusa Tenggara": ["Kota Kupang", "Kab Manggarai", "Kab Manggarai Barat", "Kab Manggarai Timur", "Kab Ngada",
                           "Kab Sumba Timur"],
    "West Kalimantan": ["Kota Singkawang", "Kota Pontianak", "Kab Ketapang"],
    "Central Kalimantan": ["Kab Kotawaringin Timur", "Kab Katingan", "Kota Palangkaraya", "Kab Barito Selatan"],
    "South Kalimantan": ["Kota Banjarmasin", "Kota Banjarbaru", "Kab Banjar", "Kab Tabalong",
                         "Kab Hulu Sungai Selatan", "Kab Tanah Bumbu"],
    "East Kalimantan": ["Kota Samarinda", "Kab Kutai Kartanegara", "Kab Kutai Timur", "Kota Bontang",
                        "Kota Balikpapan", "Kab Kutai Barat", "Kab Paser", "Kab Penajam Paser Utara"],
    "North Kalimantan": ["Kab Nunukan"],
    "North Sulawesi": ["Kota Tomohon", "Kota Manado", "Kab Minahasa", "Kab Minahasa Utara", "Kota Bitung",
                       "Kota Kotamobagu"],
    "Central Sulawesi": ["Kab Morowali", "Kab Banggai", "Kab Poso", "Kota Palu"],
    "South Sulawesi": ["Kota Makassar", "Kab Luwu Timur", "Kab Maros", "Kab Luwu Utara", "Kota Palopo",
                       "Kab Bantaeng", "Kab Luwu", "Kab Wajo", "Kota Parepare"],
    "Southeast Sulawesi": ["Kab Buton", "Kab Konawe Selatan", "Kab Wakatobi", "Kota Bau-Bau"],
    "West Sulawesi": ["Kab Majene"],
    "Gorontalo": ["Kota Gorontalo", "Kab Bone Bolango"],
    "Maluku": ["Kota Ambon"],
    "North Maluku": ["Kab Halmahera Tengah", "Kab Halmahera Timur", "Kab Halmahera Utara", "Kab Pulau Morotai",
                     "Kota Ternate", "Kab Halmahera Selatan"],
    "Papua": ["Kota Jayapura", "Kab Jayapura"],
    "West Papua": ["Kab Manokwari"],
    "Papua (Central Papua since 2022)": ["Kab Mimika"],
    "West Papua (Southwest Papua since 2022)": ["Kab Raja Ampat"],
    "South Papua (Papua until 2022)": ["Kab Boven Digoel"],
}
PROVINCE = {name: p for p, names in PROV.items() for name in names}
assert len(PROVINCE) == sum(len(v) for v in PROV.values())
EN = {"Kota Bau-Bau": "Baubau", "Kota Tanjung Pinang": "Tanjungpinang", "Kota Palangkaraya": "Palangka Raya",
      "Kab Gunung Kidul": "Gunungkidul", "Kab Toba Samosir": "Toba (Toba Samosir until 2020)"}


def place_en(name):
    kind, base = name.split(" ", 1)
    return f"{EN.get(name, base)} {'City' if kind == 'Kota' else 'Regency'}, {PROVINCE[name]}"


# rosters as printed, parsed from the saved texts
t = block("sorotan-media/gerakan-menuju-100-smart-city-diawali-dari-makassar")
mou17 = (split_list(re.search(r"tahap pertama Gerakan Menuju 100 Smart City yaitu: (.+?)\. Sedangkan", t).group(1))
         + split_list(re.search(r"pesertanya adalah (.+?)\.\n", t).group(1)))
awd17 = numbered(block("sorotan-media/langkah-menuju-100-smart-city"), 24)
mou18 = numbered(text("detik_2018-05-08.txt"), 50)
awd18 = split_list(re.search(r"diberikan penghargaan kali ini antara lain (.+?)\. \(ABPP\)",
                             block("berita-komdigi/smartcity-cara-pemerintah-layani-masyarakat-lebih-baik")).group(1))
t = text("aptika_2019-11.txt")
awd19 = [x for x in t[t.index("Berikut daftar kota / kabupaten tersebut:"):t.index("Mengawali")].splitlines()[1:] if x]
t = text("aptika_2022-07.txt")
toks = [x.strip() for x in t[t.index("Kategori"):].split("|") if x.strip()]
table2, j = [], 1
while j + 3 < len(toks) and toks[j].isdigit():
    table2.append(toks[j:j + 4])
    j += 4
awd21 = [r[1] for r in table2 if r[3] == "Masterplan Smart City 2021"]
awd22 = numbered(text("selular_2022_p2.txt"), 50)
awd23 = numbered(text("tangerangnews_2023.txt"), 50)
t = text("tanahbumbu_2024.txt")
kab24 = split_list(re.search(r"terpilih tersebut yakni (Kabupaten .+?)\.\n", t).group(1))
kota24 = split_list(re.search(r"untuk kota yakni (.+?)\.\n", t).group(1))
mou24 = [(p, canon(p, "" if p.startswith("Kabupaten ") else "Kabupaten ")) for p in kab24] + \
        [(p, canon(p, "Kota ")) for p in kota24]

R = {k: [(p, canon(p)) for p in v] for k, v in
     [("m17", mou17), ("a17", awd17), ("m18", mou18), ("a18", awd18), ("a19", awd19), ("a21", awd21),
      ("a22", awd22), ("a23", awd23)]}
R["m24"] = mou24
S = {k: [c for _, c in v] for k, v in R.items()}
for k, v in S.items():
    assert len(v) == len(set(v)), (k, [x for x, n in Counter(v).items() if n > 1])
assert [len(S[k]) for k in ["m17", "a17", "m18", "a18", "a19", "a21", "a22", "a23", "m24"]] == \
       [25, 24, 50, 50, 25, 48, 50, 50, 10]
assert set().union(*map(set, S.values())) == set(PROVINCE), \
    (set().union(*map(set, S.values())) ^ set(PROVINCE))

# MoU and award lists of 2017 and 2018 differ; the differences are fixed here so a parsing slip shows up
assert set(S["a17"]) - set(S["m17"]) == {"Kab Lombok Timur"}
assert set(S["m17"]) - set(S["a17"]) == {"Kota Singkawang", "Kab Purwakarta"}
assert set(S["a18"]) - set(S["m18"]) == {"Kota Padang Panjang", "Kota Pekalongan", "Kab Cirebon"}
assert set(S["m18"]) - set(S["a18"]) == {"Kab Banyumas", "Kota Depok", "Kab Kudus"}

# the ministry's counts are slot counts: 25 + 50 + 25 = 100 to 2019, 48 in 2021 with 7 repeats = 141, then +50, +50
award_to19 = set(S["a17"]) | set(S["a18"]) | set(S["a19"])
mou_to19 = set(S["m17"]) | set(S["m18"]) | set(S["a19"])
assert len(S["m17"]) + len(S["m18"]) + len(S["a19"]) == 100
assert len(award_to19) == 99 and len(mou_to19) == 98
REPEAT21 = {"Kab Jepara", "Kab Lombok Timur", "Kab Kutai Kartanegara", "Kab Sleman", "Kota Semarang", "Kota Mataram",
            "Kab Pasuruan"}
assert set(S["a21"]) & award_to19 == REPEAT21
assert 100 + 48 - len(REPEAT21) == 141 and 141 + 50 == 191 and 191 + 50 == 241
sp486 = block("siaran-pers/siaran-pers-no-486-hm-kominfo-12-2021-tentang-dorong-tata-kelola-pemerintahan-digital-"
              "kominfo-lakukan-pengembangan-smart-city-dan-pembangunan-pusat-data-nasional-government-cloud")
sp149 = block("siaran-pers/siaran-pers-no-149-hm-kominfo-04-2022-tentang-perluas-titik-pertumbuhan-digital-menkominfo-"
              "dorong-kolaborasi-gerakan-menuju-smart-city-2022")
assert "7 di antaranya" in sp486 and "141 Kota/Kabupaten" in sp486
assert "total 141 kabupaten kota" in sp149 and "sebanyak 191 pemerintah kabupaten dan kota" in sp149
assert "membimbing 241 kota dan kabupaten" in text("selular_2023.txt")
earlier = award_to19 | set(S["a21"])
for k in ["a22", "a23", "m24"]:
    assert not set(S[k]) & earlier, (k, set(S[k]) & earlier)
    earlier |= set(S[k])

SP223 = f"{KD}siaran-pers/siaran-pers-no-223-hm-kominfo-11-2017-tentang-tahap-pertama-gerakan-menuju-100-smart-city-" \
        "2017-24-kota-kabupaten-berhasil-menyelesaikan-smart-city-masterplan"
# round: (date, precision, MoU roster key, award roster key, source, note shared by the round)
ROUND = {
    "2017": ("2017-05-22", "day", "m17", "a17",
             f"Komdigi, {KD}sorotan-media/gerakan-menuju-100-smart-city-diawali-dari-makassar (MoU list); award list "
             f"{KD}sorotan-media/langkah-menuju-100-smart-city; Siaran Pers 223/2017, {SP223}",
             "first round; MoU signed with 25 heads of region at the kick-off in Makassar, 22 to 23 May 2017 (first "
             "day coded); 24 places completed a master plan by 15 Nov 2017 (Siaran Pers 223/2017)"),
    "2018": ("2018-05-08", "day", "m18", "a18",
             "detik.com, https://inet.detik.com/cyberlife/d-4011124/ini-50-calon-smart-city-di-indonesia-salah-satunya-"
             f"depok (MoU list); award list {KD}berita-komdigi/smartcity-cara-pemerintah-layani-masyarakat-lebih-baik",
             "second round; MoU signed by 50 mayors and regents in Jakarta on Tuesday 8 May 2018 (detik.com); the "
             "Komdigi news item prints Selasa (07/05/2018), but 7 May 2018 was a Monday; award ceremony 14 Dec 2018"),
    "2019": ("2019-05-15", "day (round under way by this date; MoU day not found)", None, "a19",
             f"Siaran Pers 100/2019, {KD}siaran-pers/siaran-pers-no-100-hm-kominfo-05-2019-tentang-dorong-pengembangan-"
             "kota-cerdas-kominfo-siapkan-asesmen-sistem-dan-infrastruktur; Antara 15 May 2019, "
             "https://www.antaranews.com/berita/870612/25-kota-dapat-pendampingan-menuju-smart-city; award list "
             "https://aptika.kominfo.go.id/2019/11/gerakan-menuju-100-smart-city-langkah-awal-wujudkan-digital-nation/ "
             "(Wayback Machine copy)",
             "third round; Siaran Pers 100/2019 (15 May 2019) puts this year's round at 25 places and Antara the same "
             "day reports Ambon chosen in it; award ceremony 6 Nov 2019"),
    "2021": ("2021-05-20", "day", None, "a21",
             f"Siaran Pers 176/2021, {KD}siaran-pers/siaran-pers-no-176-hm-kominfo-05-2021-tentang-jalin-kesepakatan-"
             "dengan-kepala-daerah-menkominfo-perluas-inisiasi-kota-cerdas-di-48-daerah; roster "
             "https://aptika.kominfo.go.id/2022/07/gerakan-menuju-100-smart-city-2/ (Wayback Machine copy), table 2, "
             "kategori Masterplan Smart City 2021",
             "MoU signed virtually with 48 regents and mayors of the national priority tourism areas (KPPN) and the new "
             "capital (IKN) area, Thursday 20 May 2021; no round in 2020"),
    "2022": ("2022-04-21", "day", None, "a22",
             f"Siaran Pers 149/2022 and 151/2022, {KD}siaran-pers/siaran-pers-no-149-hm-kominfo-04-2022-tentang-perluas-"
             "titik-pertumbuhan-digital-menkominfo-dorong-kolaborasi-gerakan-menuju-smart-city-2022; roster Selular.ID "
             "1 Dec 2022, https://selular.id/2022/12/gerakan-menuju-smart-city-2022-berhasil-jangkau-50-kota/ (page 2)",
             "MoU signed virtually with 50 regents and mayors, Thursday 21 Apr 2022"),
    "2023": ("2023-02-28", "day", None, "a23",
             "InfoPublik (Agam), https://infopublik.id/kategori/nusantara/716763/implementasi-smart-city-pemkab-agam-"
             "kementerian-kominfo-ri-teken-mou; Antara Kalsel (Hulu Sungai Selatan), https://kalsel.antaranews.com/"
             "berita/362289/kementerian-kominfo-berikan-pendampingan-hss-susun-masterplan-smart-city; roster "
             "TangerangNews 7 Dec 2023, https://www.tangerangnews.com/nasional/read/47476/50-Kota-dan-Kabupaten-Raih-"
             "Penghargaan-Gerakan-Menuju-Smart-City-2023-Ini-Daftarnya",
             "MoU on implementation signed virtually on Tuesday 28 Feb 2023 with 50 heads of region; the 50 were chosen "
             "in 2022 from 88 applicants (InfoPublik); selection letters of June 2022 (B-349/DJAI/AI.01.02/06/2022, "
             "seen in search results only) and one local paper (Tabura Pos, Oct 2023, MoU 'in 2022') give 2022, used "
             "as a sensitivity check; award ceremony 7 Dec 2023"),
    "2024": ("2024-03-05", "day", "m24", None,
             "Tanah Bumbu regency, https://mc.tanahbumbukab.go.id/pemkab-tanbu-dan-kementerian-kominfo-tandatangani-"
             "nota-kesepakatan-smart-city/; Pekalongan regency, https://dinkominfo.pekalongankab.go.id/index.php/"
             "publikasi/berita/332-penandatanganan-nota-kesepakatan-implementasi-gerakan-menuju-smart-city-oleh-"
             f"pemerintah-kabupaten-pekalongan-dengan-ditjen-aptika-kemenkominfo; Siaran Pers 43/2024, {KD}siaran-pers/"
             "siaran-pers-no-43-hm-kominfo-01-2024-tentang-optimalkan-layanan-publik-kominfo-dorong-pemda-"
             "implementasikan-smart-city",
             "MoU signed virtually on Tuesday 5 Mar 2024 by the 10 places chosen in the 2023 assessment; Siaran Pers "
             "43/2024 puts the 2024 round at 10 local governments"),
}
AWARD_ONLY = {"2017": ("2017-11-15", "day (award date; place not on the MoU list)"),
              "2018": ("2018-12-14", "day (award date; place not on the MoU list)")}
EXTRA = {("2023", "Kab Nunukan"): "; Siaran Pers 549/2023 calls it Kota Nunukan",
         ("2024", "Kab Bone Bolango"): "; listed under kabupaten",
         **{("2024", c): "; listed under kabupaten" for c in ["Kab Bangli", "Kab Gianyar", "Kab Pekalongan",
                                                               "Kab Purbalingga", "Kab Serang"]},
         **{("2024", c): "; listed under kota" for c in ["Kota Banjar", "Kota Parepare", "Kota Solok"]},
         **{("2021", c): "; one of the 7 repeat places Siaran Pers 486/2021 counts (named here by matching the "
                         "earlier award lists)" for c in REPEAT21}}

rows, seen = [], {}
for rnd, (date, prec, mk, ak, source, note) in ROUND.items():
    mou = dict((c, (i, p)) for i, (p, c) in enumerate(R[mk], 1)) if mk else {}
    awd = dict((c, (i, p)) for i, (p, c) in enumerate(R[ak], 1)) if ak else {}
    order = list(mou) + [c for c in awd if c not in mou]
    for n, c in enumerate(order, 1):
        d, pr = (date, prec) if (c in mou or not mk) else AWARD_ONLY[rnd]
        printed = (mou.get(c) or awd[c])[1]
        if mk and ak:
            roster = "roster: mou and award" if c in mou and c in awd else \
                     "roster: mou only" if c in mou else "roster: award only"
            items = "; ".join(f"{k} list item {v[c][0]}" for k, v in [("mou", mou), ("award", awd)] if c in v)
        elif ak:
            roster, items = "roster: award (no mou list found)", f"award list item {awd[c][0]}"
        else:
            roster, items = "roster: mou (no award list found)", f"mou list item {mou[c][0]}"
        spelled = [v[c][1] for v in (mou, awd) if c in v and v[c][1] in SPELL]
        extra = "".join(f"; printed as {s}" for s in dict.fromkeys(spelled))
        if c in seen:
            extra += "; earlier rounds: " + ", ".join(seen[c])
        rows.append({"economy": "Indonesia", "place_as_printed": printed, "place_en": place_en(c),
                     "area_as_printed": "", "area_scope": "whole", "project_id": f"IDSC{rnd}-{n:02d}",
                     "programme": PROG, "programme_model": MODEL, "announcement_date": d, "date_precision": pr,
                     "first_treated_year": first_treated(d), "batch": f"{rnd} round", "source": source,
                     "note": f"{SHARED}; {note}; {roster}; {items}" + extra + EXTRA.get((rnd, c), "")})
    for c in order:
        tok = "mou only" if mk and ak and c not in awd else "award only" if mk and ak and c not in mou else ""
        seen.setdefault(c, []).append(rnd + (f" ({tok})" if tok else ""))

assert len(rows) == 262, len(rows)
with open(D / "indonesia_kominfo_smart_city.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows,", len(seen), "places;", Counter(r["batch"] for r in rows))
print("first treated:", sorted(Counter(r["first_treated_year"] for r in rows).items()))
print("places in more than one round:", {c: v for c, v in seen.items() if len(v) > 1})
