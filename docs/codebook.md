# Codebook

Files in `data/final/`. Rules and sources are in `docs/dataset_plan.md` (sections named below). Years are calendar
years; an empty cell means not applicable or never.

## units.csv (one line per district unit; plan section 2b)

| Column | Meaning |
|---|---|
| unit_id | geoBoundaries shapeID, or OSM-r plus the OSM relation number for Hong Kong, Macau and South Korea (two relations joined by "+r" for the two Incheon units merged back to 2015) |
| economy, iso3 | Economy name and ISO 3166-1 alpha-3 code |
| level | ADM2; ADM3 (Philippine cities and municipalities); ADM0 (Singapore, Hong Kong, Macau) |
| name | Unit name as in the boundary file (26 blank Japanese names filled from OSM) |
| cluster_id, cluster_name | Province, prefecture or state used to cluster standard errors |
| cluster_share | Share of the unit's area inside that cluster |
| cluster_rule | overlap (largest shared area), nearest (no overlap; Wuqiu only) or city-state |
| city_state | Singapore, Hong Kong or Macau |
| area_km2 | Area on the WGS84 ellipsoid |
| uc_overlap_km2, n_uc, uc_main | Area inside 2015 urban centres (GHS-SMOD R2023A), number of centres touched, ID of the centre with the largest overlap |
| urban | Overlaps a 2015 urban centre by more than 1 m2 (design rule) |
| pop2015, pop2015_uc | GHS-POP R2023A 2015 population of the unit and of its urban centre cells (urban units and city-states only) |
| uc_pop_share | pop2015_uc / pop2015 |
| urban_city_rule | At least half of the 2015 population lives in an urban centre (Degree of Urbanisation check) |
| size_group | Quartile of pop2015 among panel units, for the size-by-year fixed effect |
| unit_flag | non_admin (lake, forest, reservoir, unassigned land) or fragment |
| in_panel | Urban, not a city-state, not flagged: the 2,256 estimation units |

## designation_links.csv (one line per designation row and unit; plan section 2c)

| Column | Meaning |
|---|---|
| unit_id, unit_name, cluster_name | Linked unit; empty for rows naming several prefectures |
| economy, file, row | Designation list and its 0-based data row in `data/raw/designations/` |
| project_id, place_en, area_scope | From the designation row (plan section 2a) |
| programme, programme_model, batch, announcement_date, date_precision | From the designation row |
| first_treated_year | Integer; January to June announcements give that year, later ones the next |
| year_flag | "month unknown, later year" when the printed year carried a condition (ASCN Dili) |
| spec | main, or the named check the row belongs to: jp_joint, jp_digital_garden, kr_campus, kr_theme_complex, my_rating_2023, ph_digital_cities, hk_kowloon_east, macau (not estimated) |
| link_rule | pin, name, Mueang district, whole cluster, single unit, prefecture only, several prefectures |
| link_flag | part when the row covers only part of the unit |
| treats | False for prefecture only and several prefectures rows |
| id_mou_only | Indonesian place on the MoU list but not the award list (2017, 2018) |
| id_alt_year | Indonesian rows: first treated year with the 2023 round moved to 2022 |

## treatment.csv (one line per unit)

Every first_treated column is the earliest first_treated_year among the unit's treating links in the stated set.

| Column | Meaning |
|---|---|
| unit_id, economy, iso3, cluster_name, urban, city_state, unit_flag, in_panel, pop2015, size_group | From units.csv |
| first_treated | Main specification, any programme model |
| first_programme, first_model | Programme(s) and model(s) of the designations in that first year |
| first_is_part | Every first-year designation covers only part of the unit |
| n_main_projects | Distinct main-specification projects linked to the unit |
| first_treated_impl, first_treated_cert, first_treated_ascn | Main specification, implementation support, certification or network membership only |
| first_treated_impl_sc, first_treated_cert_sc | As above with Super City counted as implementation support |
| first_treated_no_part | Main specification without part-area links |
| first_treated_jp_joint | Adds the four other Japanese joint-selection programmes |
| first_treated_jp_digital_garden | Adds the Digital Garden Health Special Zones |
| first_treated_kr_campus, first_treated_kr_theme_complex | Adds the Korean campus challenge or the 2019 theme complex programme |
| first_treated_my_rating_2023 | Adds the four named councils of Malaysia's 2023 rating (2024) |
| first_treated_ph_digital_cities | Adds the Philippine Digital Cities (2020) |
| first_treated_hk_kowloon_east | Hong Kong dated by the Kowloon East pilot (2015) |
| first_treated_id_2022 | Indonesia's 2023 round coded 2022 |
| first_treated_id_no_mou_only | Main specification without MoU-only Indonesian links |
| id_mou_only_unit | Treated in the main specification only through MoU-only links |
| prefecture_named_year | First year a main-specification row named only the unit's prefecture or province (for the check that drops these units from the comparison group) |

## outcomes/ (district means of the outcome grids; plan sections 3 and 4)

Files in `data/final/outcomes/`, built by `scripts/outcomes/03_combine.py` from the per-period files of
`02_extract.py`. One line per unit and period for the 2,256 panel units and the three city-states. Weights are fixed at
2015 (`01_weights.py`).

| Column | Meaning |
|---|---|
| unit_id | As in units.csv |
| year, month | Calendar year; month 1 to 12 in the monthly files |
| pm25, no2 | Mean over the unit's cells with data, each cell weighted by its GHS-POP 2015 population times the share of the cell inside the unit. PM2.5 in micrograms per cubic metre (ACAG V6.GL.03), NO2 in parts per billion (ACAG SatNO2 V4.GL.01). Empty when pop_share is below 0.5 |
| pm25_area, no2_area | The same mean with each cell weighted by its area inside the unit (check) |
| pop_share, area_share | Share of the unit's population weight, or area weight, held by cells with data |
| n_cells, n_valid | Cells touching the unit, and those with data |
| n_months | no2_annual.csv only: months with a value. no2 and no2_area are the means of the 12 monthly means and are empty unless n_months is 12 |
| min_pop_share | no2_annual.csv only: lowest monthly pop_share of the year |
| clip_share | no2_monthly.csv.gz only: share of the population weight of cells with data held by cells whose NO2 is exactly 0 in that month (estimates cut off at zero) |
| max_clip_share | no2_annual.csv only: highest monthly clip_share of the year. The main specification sets no2 missing when it is above 0.10 (registration Q12); the file keeps the value so the check that keeps every year can be run |

| File | Periods |
|---|---|
| pm25_annual.csv | 1998 to 2024 |
| pm25_monthly.csv.gz | 2005-01 to 2024-12 |
| no2_monthly.csv.gz | 2005-01 to 2024-12 |
| no2_annual.csv | 2005 to 2024 |

A cell has data when its value is not the file's fill value (PM2.5 -999.9, NO2 empty). The NO2 files also store water
and some shoreline cells as exactly 0, so a NO2 cell that is 0 in all 240 months counts as a cell with no data. A NO2
cell that is 0 in only some months is kept as a low estimate cut off at zero, and its weight counts in clip_share. The
NO2 uncertainty layer is 0.455 times the value at every level, so it is 0 wherever the value is 0 and cannot tell the
two kinds of zero apart.

`data/interim/outcomes/no2_zero_months.parquet` holds one line per cell of the weights table.

| Column | Meaning |
|---|---|
| unit_id | As in units.csv |
| row, col | Cell position on the 0.01 degree grid (row 0 at 60 degrees south, col 0 at 180 degrees west) |
| zero_months | Months from 2005-01 to 2024-12 in which the cell's NO2 value is exactly 0. A cell with 240 counts as no data |
