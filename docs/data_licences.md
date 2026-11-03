# Data licences and the public repository

Checked 2 Nov 2026 for the push to https://github.com/newlivehung123123/smart_cities_sustainability.
This is a reading of each publisher's terms for deciding what can be redistributed. It is not legal advice.
Updated 4 Nov 2026 with the covariate sources and the analysis outputs.

## 1. Data the panel is built from

| Source | Used for | Licence | Where the terms are |
|---|---|---|---|
| geoBoundaries gbOpen and gbHumanitarian, commit 9469f09 | District units and clusters | Set per file in `data/raw/boundaries/boundary_sources.csv` and `cluster_sources.csv`, and listed file by file in `NOTICE.md` | geoBoundaries metadata in `data/raw/boundaries/meta/` |
| OCHA and Humanitarian Data Exchange files | Units and clusters in Indonesia, Laos, Mongolia, the Philippines, Thailand, Timor-Leste and Vietnam | CC BY 3.0 IGO | as above |
| Open Development Cambodia, Myanmar Analytics Project | Cambodian units, Myanmar units and clusters | CC BY 4.0 | as above |
| citypopulation.de | Malaysian units | CC BY 3.0 | as above |
| Wikimedia Commons | Brunei units and clusters | Public domain | as above |
| OpenStreetMap through geoBoundaries (Wambacher), the Overpass relations in `osm/` and the Nominatim lookups in `nominatim/` | Japanese, Korean and Taiwanese units and clusters, Hong Kong and Macau units, Cambodian and Malaysian clusters, Japanese name fills | ODbL 1.0 | [openstreetmap.org/copyright](https://www.openstreetmap.org/copyright) |
| geoBoundaries Singapore ADM0 (Urban Redevelopment Authority, derived) | Singapore unit | ODbL 1.0 | geoBoundaries metadata |
| ACAG V6.GL.03 PM2.5 and ACAG SatNO2 V4.GL.01 (Washington University in St. Louis) | Outcomes | CC BY 4.0 | dataset pages, checked 1 Nov 2026 |
| GHS-SMOD R2023A and GHS-POP R2023A (European Commission JRC) | Urban centres and population weights | CC BY 4.0 | `data/raw/ghsl/ghsl_sources.csv` |
| GHS-BUILT-S R2023A (European Commission JRC) | 2015 built-up area (`built` in `data/final/covariates/light.csv`) | CC BY 4.0 | JRC data catalogue; file listed in `data/raw/ntl/ntl_sources.csv` |
| TerraClimate v1.1 (Climatology Lab, University of Idaho) | Weather covariates (`data/final/covariates/weather.csv`) | CC0 1.0 | `license` attribute of the files on the THREDDS server, checked 4 Nov 2026 |
| NASA FIRMS, MODIS Collection 6.1 active fires (MCD14ML) | Fire covariates (`data/final/covariates/fires.csv`) | NASA open data, shared without restriction | NASA Earth science data policy, checked 4 Nov 2026; files listed in `data/raw/firms/firms_sources.csv` |
| Harmonised DMSP and VIIRS night-time light, version 10 (Li et al., figshare 9828827) | Night-time light (`ntl` in `data/final/covariates/light.csv`) | CC BY 4.0 | figshare record, checked 4 Nov 2026; files listed in `data/raw/ntl/ntl_sources.csv` |
| World Bank historical income classifications, FY25 edition (`OGHIST.xlsx`) | Income group of each economy, robustness checks | CC BY 4.0 | World Bank data catalogue, checked 4 Nov 2026 |

The boundary geometry files sit in `data/interim/units/` and are not pushed. `scripts/units/` downloads them again
from geoBoundaries commit 9469f09, and `boundary_sources.csv` and `cluster_sources.csv` give the URL and SHA-256 of
each. `data/raw/boundaries/` holds those two records, the geoBoundaries metadata files, the OpenStreetMap relations,
the Nominatim lookups and `jpn_name_fill.csv` (Japanese unit names from OpenStreetMap).

geoBoundaries labels the Japanese and Taiwanese ADM2 files "Creative Commons Attribution-ShareAlike 2.0". Both
files name OpenStreetMap and Wambacher as the source, give https://www.openstreetmap.org/copyright as the licence
source, and were updated in January 2023. OpenStreetMap data have been released under ODbL 1.0 since 2012, and
geoBoundaries labels the ADM1 files from the same source ODbL 1.0. The repository therefore treats both files as
OpenStreetMap data under ODbL 1.0, and the NOTICE records the label geoBoundaries gives.

## 2. Saved copies of designation sources

Every saved copy and text extract is listed with its size, SHA-256, publisher, terms and class in
`docs/source_files.csv` (181 files). The classes are

- own, the sources_read notes written for this project (pushed),
- open, terms that allow copying and redistribution with credit (pushed),
- restricted, terms that forbid or limit redistribution (not pushed),
- unlicensed, no open licence found, so ordinary copyright applies (not pushed).

| Publisher | Files (text extracts) | Terms found | Class |
|---|---|---|---|
| Cabinet Office, Japan (chisou.go.jp and www8.cao.go.jp) | 42 (0) | Public Data License 1.0 ([chisou terms](https://www.chisou.go.jp/sousei/terms.html), [cao.go.jp rule](https://www.cao.go.jp/notice/rule.html)) | open |
| MLIT, Japan | 4 (0) | Public Data License 1.0 ([mlit.go.jp](https://www.mlit.go.jp/link.html)) | open |
| MIC, Japan | 1 (0) | Public Data License 1.0 ([soumu.go.jp](https://www.soumu.go.jp/menu_kyotsuu/policy/tyosaku.html)) | open |
| Executive Yuan, Taiwan | 4 (2) | Government Open Data License 1.0 ([ey.gov.tw](https://www.ey.gov.tw/Page/2EADDBFEDDB6357E)) | open |
| Ministry of Digital Affairs, Taiwan | 2 (1) | Government Open Data License 1.0 ([moda.gov.tw](https://moda.gov.tw/announcement/publicdeclare/951)) | open |
| HKSAR Government | 14 (7) | Copies for personal or internal use only, not for commercial use ([GovHK](https://www.gov.hk/en/about/copyright.htm)) | restricted |
| Singapore Government (MDDI, PMO) | 4 (2) | No reproduction without prior written permission ([Smart Nation terms](https://www.smartnation.gov.sg/terms-of-use/)) | restricted |
| MOLIT, Korea | 10 (0) | Pages state "All Rights reserved"; no KOGL mark | restricted |
| Open Development Laos | 2 (1) | News summaries "are copyrighted by their respective sources" | restricted |
| depa, Thailand, and city applicants | 19 (0) | None found | unlicensed |
| Indonesian government sites and Internet Archive captures | 12 (5) | None found | unlicensed |
| Indonesian news publishers | 16 (8) | None found | unlicensed |
| KPKT and local councils, Malaysia | 14 (7) | None found | unlicensed |
| DICT and PNA, Philippines (Wayback captures) | 6 (3) | None found | unlicensed |
| Vietnamese news publishers | 4 (2) | None found | unlicensed |
| ASEAN Secretariat, Malay Mail, GMA News, Macau GCS, Prime Minister of Vietnam (QD950 copy), United Nations, Eleven Myanmar | 13 (6) | None found | unlicensed |
| Washington University in St. Louis (dataset web pages in `data/raw/outcomes/sources/`) | 2 (0) | None found for the pages | unlicensed |

Ten of the PDFs were also searched for copyright or licence statements on 2 Nov 2026 (ASCN concept note, three depa
files, MSCF executive summary, DICT primer, MODA case book, two Super City council papers and the UN Mongolia file).
None states one. The two hits were body text, a mention of business licences in the DICT primer and a legal
discussion of copyright in the MODA case book.

Totals are 65 files pushed (63.1 MB) and 116 not pushed (42.1 MB).

Conditions for the pushed copies

- Public Data License 1.0 ([text](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0)) allows
  copying, redistribution, adaptation and commercial use. Each copy credits the publisher, page title and URL, and any
  edited copy says so. Section 1.7.3 states compatibility with CC BY 4.0.
- Government Open Data License 1.0 allows free, non-exclusive and sublicensable use, including reproduction and
  adaptation, with credit to the agency. The three text extracts of Taiwanese pages are edited copies made by
  `scripts/designations/totxt_helper.py` and are marked as such in the NOTICE.
- The sources_read notes quote short passages from restricted and unlicensed sources, each with its URL, to document a
  coding decision. Quotation for research with the source named is allowed under most copyright laws, so the notes
  are pushed.

## 3. Licences for the repository

| Part | Licence |
|---|---|
| `scripts/` | MIT |
| `docs/`, `data/raw/designations/*.csv` (including `link_pins.csv`), the sources_read notes, `data/raw/ghsl/ghsl_sources.csv` | CC BY 4.0 |
| `data/final/` (units, treatment, designation links, outcome tables) | ODbL 1.0 |
| `data/raw/boundaries/boundary_sources.csv`, `cluster_sources.csv` | CC BY 4.0 |
| `data/raw/boundaries/osm/`, `nominatim/`, `jpn_name_fill.csv` | ODbL 1.0 (OpenStreetMap) |
| `data/raw/boundaries/meta/` | Unchanged geoBoundaries metadata, credited to geoBoundaries |
| Pushed copies of Japanese and Taiwanese sources | Their own terms, Public Data License 1.0 or Government Open Data License 1.0 |
| `data/raw/firms/firms_sources.csv`, `data/raw/ntl/ntl_sources.csv` | CC BY 4.0 |
| `data/raw/worldbank/OGHIST.xlsx` | Unchanged World Bank copy, CC BY 4.0 |
| `data/final/covariates/` | ODbL 1.0, as part of `data/final/` |
| `outputs/analysis/` | ODbL 1.0, derived from `data/final/` |
| `exhibits/` | CC BY 4.0 |

`data/final/` holds unit names from OpenStreetMap boundaries and means computed over those boundaries, so ODbL 1.0
applies to it as a derivative database. The CC BY 4.0, CC BY 3.0 and CC BY 3.0 IGO sources allow adapted material to
be released under other terms when credit is kept, so they can sit in an ODbL database. A NOTICE file gives the
credit lines for every source in sections 1 and 2.

## 4. Not pushed

- `data/interim/` (2.7 GB). It holds the boundary geometries in `units/` (rebuilt by `scripts/units/`) and the district
  extracts in `outcomes/` (rebuilt by `scripts/outcomes/`).
- The 116 restricted and unlicensed copies and their text extracts (section 2).
- The cell values of the covariate grids saved by `scripts/covariates/` in `data/raw/terraclimate/` and
  `data/raw/ntl/` (`*.npz`), and the regional extracts of the FIRMS files in `data/raw/firms/` (`*.csv.gz`). The
  scripts download them again, and the source records give the URL and SHA-256 of each FIRMS and night-time light
  file.
- `logs/`, the run logs of the analysis.
- `ABAC smart city design v1.docx`, an internal design note.
- `paper/`, the manuscript drafts.

## 5. Rebuilding the designation lists from the repository

- Scripts 02, 03 and 09 in `scripts/designations/` run on pushed files alone.
- Script 01 needs the ASCN concept note, and scripts 04 to 08, 10 and 11 need copies that are not pushed. Each URL is
  in the designation CSVs and the sources_read notes, and the Cabinet Office URLs are in script 03. A user saves each
  copy under the path given in `docs/source_files.csv` and compares its SHA-256 with the one listed. Web pages may have
  changed since they were read on 1 Nov 2026, so their hashes may not match. The passage each coding decision rests on
  is quoted in the notes, and the coded lists are pushed.

## 6. Not checked

Statutory exemptions for official documents (Thai Copyright Act section 7, Korean Copyright Act Article 24-2) may
allow the depa notices and the MOLIT files to be pushed. Neither has been checked against the statute text, so both
stay out of the repository.
