# Dataset plan

Started 1 Nov 2026. Follows sections 4 and 5 of "ABAC smart city design v1.docx".

## 1. Order of work

| Step | Output | Status |
|---|---|---|
| 1 | Designation lists, one CSV per programme, every row sourced (`data/raw/designations/`) | Done 1 Nov 2026 |
| 2 | District units: geoBoundaries ADM2 (Philippines ADM3), Hong Kong, Macau and South Korea from OpenStreetMap, urban flag from GHS-SMOD 2015 urban centres, 2015 population (section 2b; `data/final/units.csv`, 7,163 units) | Done 1 Nov 2026 |
| 3 | Treatment table: each designated place linked to its ADM2 unit, first treated year, programme model (section 2c; `data/final/designation_links.csv`, `data/final/treatment.csv`) | Done 1 Nov 2026 |
| 4 | PM2.5 annual 1998 to 2024 and monthly 2005 to 2024, district means weighted by GHS-POP 2015 (section 4; `scripts/outcomes/01` to `03`, `data/final/outcomes/`) | Done 1 Nov 2026 (`pm25_annual.csv`, `pm25_monthly.csv.gz`) |
| 5 | NO2 monthly 2005 to 2024, annual mean of the 12 months, same weights (`no2_monthly.csv.gz`, `no2_annual.csv`) | Done 1 Nov 2026 (zero mask and clipped share, section 4) |
| 6 | Night-time light, weather and fire counts (`scripts/covariates/`, `data/final/covariates/`) | Done 3 Nov 2026, with TerraClimate in place of ERA5-Land and the harmonised series of Li et al. in place of the VIIRS composites (supplement Table S7) |
| 7 | Uncalibrated checks: MAIAC aerosol optical depth, OMI NO2 column | Not run (supplement Table S7) |
| 8 | China pilot lists and Chinese prefecture units for the replication check (supplement S2) | Not run (supplement Table S7) |
| 9 | Analysis panel, codebook (supplement S1) and checks of every merge | Done 3 Nov 2026 (`scripts/analysis/`, `outputs/analysis/`) |

## 2. Treatment coding rules (fixed before any outcome is merged)

- A district is treated from the first year any programme designates it, and stays treated.
- First treated year: the announcement year if the announcement falls from January to June, the next year otherwise. An announcement with no month known is coded to the next year, and the row is flagged.
- A designated city larger than one ADM2 unit (for example Bangkok, Jakarta, Ho Chi Minh City) treats every ADM2 unit inside that city.
- A designated area smaller than one ADM2 unit (for example Kowloon East) treats the ADM2 unit containing that area, and the row is flagged for a sensitivity check that drops it.
- Programme model, coded from the programme's own documents: implementation support (the national government funds or runs projects in the selected places), certification (a label awarded to places meeting stated criteria), network membership (ASCN).
- Each CSV row records the source URL, the date read, the page or annex number and the exact name of the place as printed.

## 2a. Designation lists (shared columns)

Every list in `data/raw/designations/` has the same columns: economy, place_as_printed, place_en,
area_as_printed, area_scope, project_id, programme, programme_model, announcement_date,
date_precision, first_treated_year, batch, source, note. area_scope is whole (the whole place
named), part (an area inside it; flagged), wider (an area reaching beyond the place named),
prefecture (only a prefecture or region is named) or unnamed (an area across several
municipalities, none named). A project in several municipalities has one row per municipality
and one shared project_id. Lists are built by `scripts/designations/` (run 01 to 11 in order); the
sources read are in `data/raw/designations/sources/`, with verbatim passages in the
`*_sources_read_*.txt` files. Japanese place_en names come from the kana readings in the MIC
municipal code list (1 Jan 2024), in Hepburn without macrons.

| File | Rows | Status |
|---|---|---|
| ascn.csv | 38 cities, July 2018 | Done |
| japan_mlit_model.csv | 52: 2019 (15 leading, 23 priority projects) and July 2020 (7 leading, 5 priority) | Done |
| japan_joint_selection.csv | 281 rows, Cabinet Office joint selection 2021 to 2025, five programmes; per-programme counts match every press release | Done |
| japan_sdgs_future_cities.csv | 287: SDGs Future Cities 216 rows (206 cities 2018 to 2024, plus 9 in 2025 and Osaka Prefecture's own row) and Municipal SDGs Model Projects 71 rows (70 projects); counts match the Cabinet Office summary and every press release | Done |
| japan_super_city.csv | 5: Super City (Tsukuba, Osaka) and the three Digital Garden Health Special Zones (sensitivity check only), 10 March 2022 | Done; programme model open (below) |
| thailand_depa_smart_city.csv | 37: every award of the smart city logo, notices of 13 Aug 2021 (5), 28 Oct 2021 (10), 27 Aug 2022 (15), 17 Aug 2023 (6) and 4 Sep 2025 (1, after the panel); counts match the depa page and the 2023 index | Done |
| korea_molit_smart_city.csv | 87 rows, 85 projects: National Pilot Smart Cities (2, Jan 2018), Smart Challenge 2019 (10), 2020 main (7) and round (18), 2021 (45: 23 solution diffusion, 6 main, 8 campus, 4 town, 4 city), and the 2019 theme complex construction programme (3, sensitivity check only); counts match every release | Done |
| indonesia_kominfo_smart_city.csv | 262 rows, 251 places: Gerakan Menuju (100) Smart City rounds of 2017 (25 MoU, 1 award only), 2018 (50 MoU, 3 award only), 2019 (25), 2021 (48), 2022 (50), 2023 (50) and 2024 (10); the 100, 141, 191 and 241 slot counts in the ministry's releases are all reproduced | Done |
| malaysia_kpkt_smart_city.csv | 29: Malaysia Smart City Framework pilot cities (5, launched 23 Sep 2019), smart city rating of councils 2023 (4 of 25 to 29 named, roster partial) and 2024 (20, full annex list, after the panel); counts match every KPKT release | Done |
| Vietnam (no file) | none: Decision 950/QĐ-TTg (1 Aug 2018) names no pilot places; provinces adopted their own schemes (34 approved by Feb 2023, 37 by Aug 2025), which is self-selection; treated places are the ASEAN Smart Cities Network members only | Done (sources file only) |
| philippines_dict_digital_cities.csv | 31 rows, 25 locations: Digital Cities 2025 (DICT, IBPAP, LPC, launched 30 Jun 2020), three clusters split into their local government units; the PNA, GMA and DICT primer lists match; IT-BPM hub programme, sensitivity check only | Done |
| Taiwan (no file) | none: the 普及智慧城鄉生活應用計畫 (from 2018) funds firms and names no place; all 22 counties and cities sit on its Executive Yuan platform and 2018 local project titles already name 16 of them; coded nationwide; `09_taiwan.py` checks the counts and writes no file | Done (sources file only) |
| hongkong_singapore_smart_city.csv | 3: Singapore Smart Nation (launch 24 Nov 2014, first treated 2015), Hong Kong Smart City Blueprint (15 Dec 2017, first treated 2018) and Kowloon East pilot area (2015 Policy Address, 14 Jan 2015, sensitivity check only) | Done |
| macau_smart_city.csv | 1: Macao's Framework Agreement of Strategic Cooperation on Smart City Development with Alibaba Group (4 Aug 2017, first treated 2018); Macau is not estimated and is kept out of the donor pools | Done |
| Mongolia, Timor-Leste, Brunei, Cambodia, Laos, Myanmar (no file) | none: no national list naming places found; treated places are their ASCN members (Dili 2026, after the panel); city or provincial plans are self-adoption and not coded (Others_sources_read_2026-11-01.txt) | Done (sources file only) |

**Japan coding decision (1 Nov 2026).** From FY2021 MLIT selects its smart city projects through
a joint Cabinet Office review of five programmes. The main specification keeps one programme,
the MLIT smart city programme (Model Projects 2019 and 2020; スマートシティモデルプロジェクト 2021;
renamed スマートシティ実装化支援事業 from 2022, which the annexes state is the same programme).
The other four (Cabinet Office future technology, MIC smart city, METI and MLIT MaaS) are kept
in japan_joint_selection.csv for a sensitivity check that treats a place selected by any of the
five. Most MLIT places after 2020 repeat earlier ones, so only their first selection sets
first_treated_year. The design's Table 1 line "5 added (2021)" is the five 2020 priority
projects; Table 1 needs that correction.

**Japan SDGs and Super City coding (1 Nov 2026).** SDGs Future Cities are coded certification
(a label, with one extra grant application allowed) and Municipal SDGs Model Projects
implementation support (a subsidy of up to 20 million yen per city). Super City is coded
certification for now: the designation release names regulatory reform and no funding, but
the zone councils' timeline records Cabinet Office survey projects (調査事業) adopted in July
2022 and July 2023 without naming the places. If those went to the designated zones, the rule
in section 2 makes Super City implementation support. The main specification codes certification and a check
codes implementation support (section 6).

**Thailand coding (1 Nov 2026).** The depa notices are page scans, read from page images. Each
awards a logo valid two years and names no funding, so the programme is coded certification. The
announcement date is the date each notice was signed, from which the logo applies; all fall in
July to December, so first_treated_year is 2022, 2023 or 2024. Thirteen projects name only a
province; their project areas come from the depa executive summaries when units are linked.

**Korea coding (1 Nov 2026).** Rows come from the MOLIT releases on korea.kr (KOGL Type 1) and
Wayback copies of the MOLIT smart city portal. Every programme funds projects in the selected
places, so all rows are implementation support. Every release falls in January to June, so
first_treated_year is the release year. Main projects in 2020 and 2021 repeat earlier preliminary
places and do not move the treated year. The 2019 town master plans are coded with the Smart
Challenge because the 2020 release counts them among its 2019 preliminary projects. The campus
challenge and the 2019 construction programme are kept for sensitivity checks only. The design's
Table 1 line "45 sites" is the 2021 round only; 2019 to 2021 give 73 selections (10, 18, 45),
and Table 1 needs that correction.

## 2b. District units (decided 1 Nov 2026)

- Boundaries come from geoBoundaries gbOpen, pinned to commit 9469f09, at ADM2 for Japan, South Korea, Taiwan, Mongolia,
  Brunei, Cambodia, Indonesia, Laos, Malaysia, Myanmar, Thailand, Timor-Leste and Vietnam. The Philippines use ADM3 (cities
  and municipalities), because geoBoundaries ADM2 for the Philippines are provinces and Philippine programmes name cities.
  Singapore uses ADM0 (Urban Redevelopment Authority outline, 724 km2).
- Hong Kong and Macau are not in geoBoundaries as economies, and its China ADM1 file draws Macau with five points and
  96 km2. Both outlines come from OpenStreetMap relations 913110 (Hong Kong, version 225) and 1867188 (Macau, version 114),
  read from the OSM API on 1 Nov 2026 (ODbL 1.0). The outlines include territorial waters (2,756 and 116 km2). Population
  weights are zero at sea, so the weighted means are unaffected; the unweighted check for the two excludes cells with no
  2015 population.
- South Korea (changed 1 Nov 2026): the gbOpen ADM2 file (from citypopulation.de) lies about 1 km off the true outlines;
  four Seoul districts overlap their OpenStreetMap outlines by only 42 to 57 percent (area overlap over union), too far for
  0.01 degree outcome cells. The Korean units are therefore the OSM admin_level 6 districts (si, gun, autonomous gu) plus
  Sejong, listed as the subareas of the province relations (Overpass refused or timed out), checked for land left in
  no district, and read from the OSM API (ODbL 1.0, gzipped copies kept). The check found two districts missing from
  those lists (Cheorwon-gun, relation 2505634; Ulsan Nam-gu, 8127814), now added; what remains outside every district is
  3,935 km2 of sea off North Gyeongsang that the province outline includes, with no land (gbOpen ADM1 shrunk by 2 km).
  The Korean units nest fully in the OSM 2015 provinces (lowest share 1.000). Incheon's July 2026 districts
  are merged back to 2015 extents: Jemulpo-gu with Yeongjong-gu (together the 2015 Jung-gu and Dong-gu, which cannot be
  separated again, so they form one unit) and Seohae-gu with Geomdan-gu (the 2015 Seo-gu). Expected count 228. Malaysia's
  citypopulation.de file was checked the same way and is accurate (Kuala Lumpur overlap 0.97); Putrajaya is not a unit
  of that file and lies inside Sepang.
- Japanese names: 26 gbOpen units have blank or question-mark names. Each is filled from one Nominatim reverse lookup
  at its representative point (scripts/units/05_jpn_names.py, data/raw/boundaries/jpn_name_fill.csv); all 26 fall in
  their own prefecture and overlap the returned OSM outline by 94 to 100 percent.
- Units that are not administrative areas cannot be designated and are flagged non_admin and left out of the estimation
  panel: Chiba's land of undetermined affiliation (所属未定地), and Indonesia's Danau, Danau Toba, Hutan and Waduk Cirata
  (lakes, a forest and a reservoir). Three of them overlap an urban centre (2015 population 1, 78 and 1,807).
- A 0.17 km2 piece of Saitama City that gbOpen keeps as a separate unit (its name filled as Saitama) is flagged fragment
  and left out of the panel too; the rest of Saitama City is its own unit.
- `scripts/units/06_flags.py` (run after 04_population.py) writes unit_flag and in_panel into units.csv. The estimation
  panel is every urban unit that is not a city-state and not flagged: 2,256 units (4 flagged urban units removed). Size
  groups are recomputed on the panel; bounds 281 to 71,196; 71,314 to 152,663; 152,703 to 294,161; 294,393 to 5,440,130.
- Feature counts can differ from the geoBoundaries metadata count (Japan 1,742 against 1,745; South Korea 228 against 229;
  Taiwan 368 against 369; Malaysia 159 against 160; Philippine provinces 86 against 87). Both counts are kept in
  boundary_sources.csv.
- Clusters for standard errors: ADM1 (province, prefecture, state); in the Philippines the province (geoBoundaries ADM2);
  each city-state is its own cluster. Several gbOpen ADM1 files are coarser than the unit files (South Korea from Natural
  Earth put Daejeon's Dong-gu in South Chungcheong; Vietnam from a 2008 map with 64 provinces), so 01b_clusters.py scores
  every candidate cluster file by how cleanly it nests the units (units whose second largest overlap exceeds half the
  largest, then units with less than 0.9 of their area in one cluster) and keeps the best: gbHumanitarian ADM1 for
  Mongolia, Indonesia, Laos, Thailand, Timor-Leste and Vietnam; gbOpen for Japan, Taiwan, Brunei, Cambodia, Malaysia,
  Myanmar and the Philippines; for South Korea the 2015 provinces rebuilt from OSM (Gwangju as the union of its five
  districts, South Jeolla as the 2026 Jeonnam-Gwangju province minus Gwangju, Gunwi-gun moved from Daegu back to North
  Gyeongsang, where it was until 1 July 2023). Scores are in `data/raw/boundaries/cluster_sources.csv`. Each unit takes
  the cluster with which it shares the most area; a unit in no cluster (only Wuqiu, a 0.9 km2 islet of Kinmen) takes the
  nearest and is flagged `cluster_rule = nearest`.
- Urban centres: GHS-SMOD R2023A, 2015 epoch, class 30 (urban centre grid cell) on the 1 km Mollweide grid, grouped into
  centres by edge contiguity (no diagonals), the GHSL rule. The design named GHS-UCDB R2024A, but that release draws its
  centres on the 2025 epoch, after most designations; SMOD R2023A 2015 applies the same rule in 2015 and comes from the same
  release as the GHS-POP weights.
- A unit is urban if its area overlaps a 2015 urban centre by more than 1 m2 (design rule; the threshold removes only
  numerical noise, and touching at a border does not count). The overlap
  in km2 and the share of the unit's 2015 population living in urban centre cells are stored. A check uses the Degree of
  Urbanisation city rule instead: at least 50 percent of the unit's 2015 population in an urban centre.
- Population: GHS-POP R2023A, 2015 epoch, 3 arc-second grid in WGS84, 10-degree tiles. Twelve 3 arc-second cells span one
  0.01 degree outcome cell, but the GHS-POP cell edges sit half a cell off the 0.01 degree edges, so each outcome cell sums
  its 11 by 11 inner cells, half of each edge cell it shares and a quarter of each corner cell. Tiles are read inside the
  zip, summed onto the 0.01 degree grid of the study window and deleted. Only tiles that meet an urban unit or a city-state
  are fetched. JRC serves each connection at about 0.1 MB/s, so tiles are fetched over several connections. A 3 arc-second
  cell counts towards a unit's population (and urban-centre population) when its centre falls inside the unit (and inside
  an urban centre).
- Size groups for the size-by-year fixed effect: quartiles of 2015 population among the urban units of the estimation
  sample, pooled across economies.
- Files: `data/raw/boundaries/boundary_sources.csv` (economy, level, source, licence, year represented, URL, SHA-256,
  date read); `data/interim/units/` (one GeoParquet per economy, raw GeoJSON deleted after conversion);
  `data/interim/units/urban_centres_2015.parquet`; `data/final/units.csv` (one row per unit, no geometry).

## 2c. Linking designations to units, and the treatment tables (1 Nov 2026)

- `scripts/treatment/01_link.py` links each designation row to the units it treats. Rules in order: hand pins; the
  single unit of Singapore, Hong Kong and Macau; rows naming only a prefecture or province (listed with every unit of
  it, treating none); rows naming several prefectures (no unit); then the place name, matched inside the prefecture
  named after the comma when there is one. Names are compared after removing accents, bracketed text, punctuation and
  administrative words; Korean, Japanese and Thai suffixes are removed only in their own country. Japanese names are
  folded from Hepburn to Kunrei on both sides, because gbOpen spells them both ways. In Indonesia "City" means the Kota
  unit, and a bare name (network members only) is tried as Kota first. In Thailand a municipality named after its
  province lies in the Mueang district. A whole-area city larger than one unit (Bangkok, Busan, Ha Noi) treats every
  unit of its province. A name that matches no unit, or more than one, must be pinned.
- Hand pins: `data/raw/designations/link_pins.csv`, 77 pins, each with its reason: project areas inside or across
  units, Japanese names that occur twice in one prefecture, gbOpen misspellings (Omuta is stored as Oomura) and cities
  spanning several units (Yangon). `02_pins.py` resolves each pin through one Nominatim search in the pin's country
  (an outline treats the units at least half inside it; a road or canal treats the units holding 5 percent of a 250 m
  strip around it), or by unit or province name where the source names them.
- Thai projects named only by province (13 rows). depa's executive summaries (bare depa.or.th, saved in
  `data/raw/designations/sources/depa_summaries/`) were read for the area of each. Seven have one, and each pin cites
  its page: Lampang 2023 names five pilot districts (Mueang Lampang, Ko Kha, Hang Chat, Chae Hom, Soem Ngam, 4,015
  km2); Samut Prakan 2023 (1,004 km2) and Chachoengsao 2021 (5,351 km2, 720,698 people) print the whole province;
  Nakhon Sawan 2021 is the city municipality (27.87 km2, Mueang district); Trang 2021 is three municipalities (37.81
  km2), the two named lying in Mueang Trang; Khon Kaen 2021 prints no area but is led by the city municipality, so
  Mueang Khon Kaen; Phuket 2021 prints no area but names services in all three districts (the city and Wichit
  municipalities, Patong and Kathu, the light rail from the airport in Thalang). The last four are flagged part. The
  Thinicon Valley summary (Phuket 2025) prints 2.08 km2 in Wichit subdistrict, Mueang Phuket. The six projects of 27
  Aug 2022 (Phitsanulok, Nakhon Ratchasima, Ubon Ratchathani, Krabi, Phang Nga, Satun) have no summary on the depa
  page, and the 2023 index gives only their names and scores, so they stay prefecture only; Phitsanulok city has its
  own 2022 row.
- Result: all 1,113 rows link, none unmatched. 942 by name, 89 by pin, 14 to a Mueang district, 12 to every unit of a
  city larger than one unit, 5 city-state rows, 45 prefecture only, 6 several prefectures; 1,841 units appear in a
  link. 128 rows cover only part of their unit and are flagged part.
- Geographic check (`03_check_links.py`, `data/interim/treatment/link_check.csv`): up to 15 places per economy are
  drawn from the name links (84 places, seed 1), looked up in the source's own script, and the unit holding the returned
  outline or point is compared with the linked unit. The first run found two link errors, both fixed: Chiang Mai had
  linked to Si Chiang Mai in Nong Khai (the Korean suffix "si" was removed from Thai names), and the network member
  Semarang to Semarang Regency instead of the city. After the fix 83 places are found and 76 agree. The other seven are
  geocoder answers, not link errors: the province outline for Battambang, Rayong, Phuket and Chonburi; a different
  서산 near Gyeongju; a point in Mexico municipality just outside San Fernando, Pampanga; and the regency for a bare
  "Solok" where the source names Solok City.
- `04_treatment.py` writes `data/final/designation_links.csv` (2,967 lines, one per designation row and unit) and
  `data/final/treatment.csv` (one line per unit); columns are in `docs/codebook.md`. Each row is given the main
  specification or one named check (section 6). A link treats its unit unless the row is prefecture only or several
  prefectures. ASCN Dili ("2027 if after June") is coded 2027, after the panel, and flagged. Indonesian places on the
  MoU list only are flagged (10 units), and the 2023 round carries 2022 as its alternative year.
- Main specification: 640 of the 2,256 panel units are treated, 619 by 2024. First treated years in the panel: 2017
  (25), 2018 (235), 2019 (63), 2020 (49), 2021 (79), 2022 (70), 2023 (63), 2024 (35), 2025 (13), 2026 (4), 2027 (4).
  By economy (treated by 2024 of panel units): Indonesia 225 of 344, Japan 134 of 640, Thailand 76 of 152, South Korea
  68 of 136, Vietnam 61 of 304, Philippines 16 of 323, Cambodia 14 of 28, Laos 7 of 12, Myanmar 7 of 57, Brunei 6 of
  12, Malaysia 5 of 52, Timor-Leste 0 of 4, Mongolia 0 of 7, Taiwan 0 of 185.

## 3. Outcome data, checked 1 Nov 2026

| Variable | File | Grid | Notes |
|---|---|---|---|
| PM2.5 annual | ACAG V6.GL.03, `satpmdata.s3.amazonaws.com/V6GL03/CNNPM25/Annual/GL/`, 1998 to 2024, about 445 MB per year | 0.01°, 13,000 × 36,000 cells, latitude 60°S to 70°N, chunks 1,182 × 3,273 | The Asia file (AS) covers only 10°S to 60°N and 65°E to 145°E, which excludes Kupang (10.2°S) and eastern Hokkaido, so the global file is read instead |
| PM2.5 monthly | Same version, `Monthly/` | 0.01° | Used for the Singapore burning-season check only |
| NO2 at ground level | ACAG SatNO2 V4.GL.01, `satpmdata.s3.amazonaws.com/SATNO2V4GL01/NO2/YYYY/`, 240 monthly files 2005 to 2024, about 790 MB each | Same 0.01° grid as PM2.5, chunks 512 × 512, gzip | Variables NO2 (ppb) and NO2_uncertainty |

Both are netCDF4 (HDF5) files. h5py with the ros3 driver reads the byte range of each chunk
from the file index; only the chunks that hold a cell of a panel unit or city-state are then
downloaded by HTTP range requests, inflated with zlib and unshuffled, so no file is stored. The
first period of every run is checked against h5py's own reading of one chunk
(`scripts/outcomes/02_extract.py`). PM2.5 fill value is -999.9 and NO2 fill value is NaN.

Licences and citations: both products are CC BY 4.0. PM2.5 V6.GL.03 is cited as Shen et al.
(2024), ACS ES&T Air 1(5), 332-345, doi 10.1021/acsestair.3c00054. SatNO2 V4.GL.01 is cited as
Yan et al. (2026), Scientific Data, doi 10.1038/s41597-026-08329-2, with the Zenodo record
10.5281/zenodo.19740022 (Zenodo holds 2005 to 2023; the S3 bucket, used here, holds 2005 to 2024).

## 4. District means

Each grid cell is weighted by the GHS-POP 2015 population inside that cell multiplied by the
fraction of the cell inside the district (exactextract). The unweighted area mean is kept as
a check. A district-year is recorded as missing when cells with data cover less than 50
percent of the district's 2015 population.

Weights (`scripts/outcomes/01_weights.py`, 1 Nov 2026) cover 2,259 units, the 2,256 panel
units and the three city-states, in 1,861,227 unit-cell pairs (median 138 cells per unit,
range 2 to 36,973). The population implied by the weights has a median ratio to pop2015 in
`units.csv` of 0.996 (5th percentile 0.908, 95th percentile 1.063), and the weights hold 99.0
percent of all pop2015. The 29 units outside 0.8 to 1.25 are small or coastal (median area
12 km² against 114 km² for all units), where 3 arc-second population near a boundary or the
coast falls in 0.01° cells that the unit covers only in part. The ratio changes the weighted
total but not the set of cells behind each mean, so these units are kept.

PM2.5 annual (`data/final/outcomes/pm25_annual.csv`, 1 Nov 2026) has 60,993 rows, 2,259 units
over 27 years. Each year needed 10 chunks (about 50 MB) and took 11 to 532 seconds. No
unit-year is missing and no cell value is negative; in 81 unit-years some cells lack data, and
those cells hold no 2015 population (pop_share is 1 in every row). District means run from 2.4
to 92.0 µg/m³, and the population-weighted and area-weighted log means correlate at 0.987 (median
absolute log difference 0.011). The median district mean by year runs from 12.5 µg/m³ (1999) to
20.0 µg/m³ (2014). NO2 needs 66 chunks (about 19 MB) per month.

PM2.5 monthly (`data/final/outcomes/pm25_monthly.csv.gz`, 1 Nov 2026) has 542,160 rows, 2,259
units over 240 months, with no missing unit-month and no restart of the run. Two cells in
October 2010 are negative and are kept; no district mean is at or below zero. District means
run from 0.54 to 380.34 µg/m³; the five highest are Kalimantan and Sumatra districts in the
fire months of 2006, 2009 and 2015 (Hulu Sungai Selatan in October 2006, Kota Palangka Raya in
September 2015). The mean of a district's 12 monthly means matches its annual
mean in `pm25_annual.csv` to within 6 × 10⁻⁶ in logs (median 1.3 × 10⁻⁶) for all 45,180
unit-years, so the annual files are the average of the monthly files and the two downloads
agree.

NO2 monthly (`data/final/outcomes/no2_monthly.csv.gz`, 1 Nov 2026) has 542,160 rows, 2,259 units over 240 months, and
`no2_annual.csv` has 45,180 unit-years. SatNO2 stores water and some shoreline cells as exactly 0 in place of a fill
value. A first run counted those cells as 0 ppb, and Cavite City came out at 0.075 ppb. 49,587 cells (1.64 percent of
the weighted population) are 0 in all 240 months and now count as no data. Another 528,319 cells (1.32 percent) are 0 in
1 to 239 months, only from 2005 to 2016 and mostly in 2007, 2009 and 2014, in rural Indonesia (317,570 cells) and
Myanmar (187,551). Their median non-zero value is 1.39 ppb against 2.28 ppb for all cells, and cells at 0 in June 2007
read 0.50 ppb in June 2006, 0.44 in June 2008 and 0.25 in June 2010, so these zeros are low estimates cut off at zero
and are kept. The NO2 uncertainty layer is 0.455 times the value at every level and cannot tell the two kinds of zero
apart. The first run's outputs are kept in `data/interim/outcomes/no2_zeros_as_data/` for the comparison below.

Compared with the first run, the mask increases the mean of 397 units by more than 1 percent (median log change among
changed rows 0.051, 90th percentile 0.263, maximum 0.590) and never lowers a mean. Missing unit-years in `no2_annual.csv`
go from 82 to 362. Eighteen panel units have no NO2 in any year, because cells with data hold less than half of their
population weight (14 of them have more than half in masked cells): Saka, Utadu, Kepulauan Aru, Kota Ternate, Lembata,
Kota Baubau, Cavite City, Samal, Balamban, Tagbilaran City, Magallanes, Qijin, Zhongzheng (Keelung), Van Don, Kien Luong,
Son Tra, Putatan and Gwangyang-si. NO2 shows no break around 2018, when TROPOMI data begin (median year-over-year log
change +0.008), and the median district mean falls from 9.01 ppb (2005) to 6.78 ppb (2024).

Cut-off zeros make some rural district means very low (Paniai 2014, 0.003 ppb). `clip_share` in the monthly file is the
share of the population weight of cells with data held by cells at 0, and `max_clip_share` in the annual file is its
highest month. No month from 2017 on has a cell at 0 outside the mask. Of the 45,068 panel unit-years, 1,230 with a
value have some cut-off cell, and max_clip_share is above 0.01 in 427 (149 units), 0.05 in 190 (86), 0.10 in 109 (57),
0.25 in 38 (26) and 0.50 in 19 (14). The 109 above 0.10 fall from 2005 to 2015 (42 in 2014, 23 in 2007, 17 in 2015, 14
in 2009) and are Indonesian (84), Myanmar (20), Philippine (2), Lao, Thai and Vietnamese (1 each). The main
specification sets these 109 unit-years missing and a check keeps them (section 6, registration Q12 and Q24). With the
rule the lowest annual mean is 0.31 ppb (Kepulauan Yapen 2014) and 13 unit-years are below 0.5 ppb, against 58 without
it.

## 5. Public repository

https://github.com/newlivehung123123/smart_cities_sustainability holds the dataset, the scripts, the analysis
outputs and the exhibits. Licences were checked on 2 Nov 2026 and updated on 4 Nov 2026 (`docs/data_licences.md`,
with every saved copy listed in `docs/source_files.csv`). 65 saved copies are pushed and 116 restricted or
unlicensed copies are not. The licence of each part is set out in `LICENSE.md`, `scripts/LICENSE` (MIT) and
`NOTICE.md` (credit lines). `data/interim/`, the raw covariate grids and the manuscript are not pushed.

## 6. Decisions, 1 and 2 Nov 2026

- Indonesia Gerakan Menuju Smart City is coded implementation support.
- Indonesia 2023 round: the MoU was signed virtually on 28 Feb 2023 (InfoPublik, Antara Kalsel), so the round codes 2023 under
  the section 2 rule. The June 2022 selection letters and one report of a 2022 signing give 2022, used as a sensitivity check.
- Indonesia 2017 and 2018 have MoU and award lists that differ. Places on the MoU list only keep the MoU date and are flagged;
  a sensitivity check drops them. Award-only places take the award date. The 2018 MoU is dated 8 May 2018 (Tuesday), not
  Komdigi's "Selasa (07/05/2018)". A 2024 round (10 places, MoU 5 Mar 2024) was found and added.
- Malaysia Smart City Framework pilot cities are coded implementation support, dated by the launch (23 Sep 2019), so first
  treated 2020. Four of the five are also ASEAN Smart Cities Network members from 2018; Kulim is the only new place.
- Malaysia's smart city rating (Penarafan Bandar Pintar) is coded certification. The 2023 round (9 Nov 2023, first treated 2024)
  rated 25 to 29 councils and only 4 are named, so the main specification drops Malaysian unit-years in 2024; a sensitivity
  check keeps them with the 4 named councils treated. The 2024 round (20 councils) starts after the panel.
- Vietnam has no national designation list: Decision 950/QĐ-TTg (1 Aug 2018) leaves pilot areas to later selection and none
  was found, and provincial schemes are self-selected. Treated places are the three ASEAN Smart Cities Network members (2018).
  Because most provinces adopted their own schemes from about 2019, a sensitivity check drops Vietnam's untreated districts
  from the control group.
- Philippines Digital Cities 2025 (30 Jun 2020) is an IT-BPM hub programme, not a smart city programme, so the main
  specification does not code it (Philippine treated places are the ASEAN Smart Cities Network members). Two sensitivity
  checks: the 25 locations coded treated from 2020 as implementation support, and the 25 locations dropped from the control
  group. The Philippine unit is ADM3 (section 2b).
- Taiwan's smart city programme (普及智慧城鄉生活應用計畫, from 2018) is nationwide: it funds firms, names no place, and all 22
  counties and cities sit on its platform. Taiwan has no designated place, so under economy-by-year fixed effects it adds no
  identifying variation. No county-level staggered coding is built, because 28 of the 55 local project titles of 2018 name no
  county. Taiwan's districts stay in the Singapore and Hong Kong donor pools; a sensitivity check drops them.
- Singapore and Hong Kong are coded "whole-city strategy" (one unit each, synthetic control only). Singapore is dated by
  the Smart Nation launch (24 Nov 2014); the National Day Rally (17 Aug 2014) gives the same first treated year, 2015.
  Hong Kong is dated by the Blueprint (15 Dec 2017, first treated 2018); a sensitivity check uses the Kowloon East pilot
  area of the 2015 Policy Address (first treated 2015). Blueprint 2.0 (Dec 2020) is not a new designation.
- Japan Super City: certification in the main specification; a sensitivity check codes it implementation support. Both are reported.
- NO2 zeros. A cell that is 0 in all 240 months is water or shoreline and counts as no data. A cell that is 0 in only some
  months is a low estimate cut off at zero and is kept. The main specification sets a NO2 district-year missing when the
  clipped share is above 0.10 in any month, and a check keeps every district-year (registration Q12 and Q24). At 0.10,
  cut-off cells whose true values are at most 0.5 ppb lower a district mean of at least 1 ppb by at most about 5 percent,
  the smallest effect of interest. The rule was fixed on 2 Nov 2026.
- Analysis plan: `docs/osf_registration.md`, written before any outcome was merged with the treatment table and cited
  in the paper as https://osf.io/86wbz.
- Design Table 1 corrections (Japan "5 added (2021)", Korea "45 sites") are made in the paper's Table 1.
- Disk: grids are read by HTTP range requests and never stored whole; only district-level extracts are kept. GHS-POP is
  fetched only for the tiles covering the study region and deleted once the district weights are saved. If space runs short,
  process one year at a time and delete each year's intermediates.
