# Notice

This repository holds material from the third-party sources below, or values derived from them. Each is credited
here as its licence requires. Licences of the repository's own parts are in `LICENSE.md`, and the checks behind
this list are in `docs/data_licences.md`.

## OpenStreetMap

© OpenStreetMap contributors. Available under the Open Database License 1.0, https://www.openstreetmap.org/copyright.

OpenStreetMap data are in `data/raw/boundaries/osm/` (Overpass relation downloads), `data/raw/boundaries/nominatim/`
(Nominatim lookups) and `data/raw/boundaries/jpn_name_fill.csv`. Through geoBoundaries they also give the Japanese,
Korean and Taiwanese units and clusters, the Hong Kong and Macau units and the Cambodian and Malaysian clusters.
Values derived from them are in `data/final/`.

geoBoundaries labels its Japanese and Taiwanese ADM2 files (source "OpenStreetMap, Wambacher")
"Creative Commons Attribution-ShareAlike 2.0". This repository treats both as OpenStreetMap data under ODbL 1.0,
the licence of OpenStreetMap since 2012.

## geoBoundaries

Runfola, D., Anderson, A., Baier, H., et al. (2020). geoBoundaries: A global database of political administrative
boundaries. PLOS ONE, 15(4), e0231866. https://doi.org/10.1371/journal.pone.0231866

Boundary files were taken from https://github.com/wmgeolab/geoBoundaries at commit 9469f09, with the URL and SHA-256
of each in `data/raw/boundaries/boundary_sources.csv` and `cluster_sources.csv`. The geometry files are not
redistributed here. `data/final/` holds unit names, areas and district means derived from them. Each file keeps
the licence of its original source.

| Economy | Level | Use | Source named by geoBoundaries or OpenStreetMap | Licence as labelled by the source |
|---|---|---|---|---|
| Japan | ADM2 | unit | OpenStreetMap, Wambacher | Creative Commons Attribution-ShareAlike 2.0 |
| Japan | ADM1 | cluster | OpenStreetMap, Wambacher | Open Data Commons Open Database License 1.0 |
| South Korea | ADM2 | unit candidate, not used | geoBoundaries, citypopulation.de | Creative Commons Attribution 3.0 License |
| South Korea | ADM1 | cluster candidate, not used | Natural Earth | Public Domain |
| South Korea | ADM2 | unit | OpenStreetMap admin_level 6 relations listed as subareas of the province relations on 2026-11-01, plus relations 2505634, 8127814, plus Sejong (relation 2349795); versions 3 to 66; Incheon merged to 2015 extents (Jemulpo-gu and Yeongjong-gu; Seohae-gu and Geomdan-gu) | Open Data Commons Open Database License 1.0 |
| Taiwan | ADM2 | unit | OpenStreetMap, Wambacher | Creative Commons Attribution-ShareAlike 2.0 |
| Taiwan | ADM1 | cluster | OpenStreetMap, Wambacher | Open Data Commons Open Database License 1.0 |
| Mongolia | ADM2 | unit | National Statistical Office of Mongolia, OCHA ROAP | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Mongolia | ADM1 | cluster candidate, not used | OpenStreetMap, Wambacher | Open Data Commons Open Database License 1.0 |
| Brunei | ADM2 | unit | geoBoundaries, Wikimedia Commons; credit to user 'Rarelibra' | Public Domain |
| Brunei | ADM1 | cluster | geoBoundaries, Wikimedia Commons; credit to user 'Tachymetre' | Public Domain |
| Cambodia | ADM2 | unit | Open Development Mekong, Open Development Cambodia | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| Cambodia | ADM1 | cluster | OpenStreetMap, Wambacher | Open Data Commons Open Database License 1.0 |
| Indonesia | ADM2 | unit | Badan Pusat Statistik (BPS - Statistics Indonesia), World Food Programme, OCHA ROAP | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Indonesia | ADM1 | cluster candidate, not used | OpenStreetMap, Wambacher | Open Data Commons Open Database License 1.0 |
| Laos | ADM2 | unit | National Geographic Department, OCHA ROAP | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Laos | ADM1 | cluster candidate, not used | OpenStreetMap, Wambacher | Open Data Commons Open Database License 1.0 |
| Malaysia | ADM2 | unit | geoBoundaries, citypopulation.de | Creative Commons Attribution 3.0 License |
| Malaysia | ADM1 | cluster | OpenStreetMap, Wambacher | Open Data Commons Open Database License 1.0 |
| Myanmar | ADM2 | unit | Myanmar Analytics Project, USAID/Burma | Creative Commons Attribution 4.0 (CC BY 4.0) |
| Myanmar | ADM1 | cluster | Myanmar Analytics Project, geoBoundaries | Creative Commons Attribution 4.0 (CC BY 4.0) |
| Thailand | ADM2 | unit | Royal Thai Survey Department, OCHA ROAP | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Thailand | ADM1 | cluster candidate, not used | OpenStreetMap, Wambacher | Open Data Commons Open Database License 1.0 |
| Timor-Leste | ADM2 | unit | WHO, OCHA ROAP | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Timor-Leste | ADM1 | cluster candidate, not used | OpenStreetMap, Wambacher | Open Data Commons Open Database License 1.0 |
| Vietnam | ADM2 | unit | OCHA ROAP, Government of Viet Nam | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Vietnam | ADM1 | cluster candidate, not used | geoBoundaries, Wikipedia | Public Domain |
| Philippines | ADM3 | unit | National Mapping and Resource Information Authority (NAMRIA), Philippines Statistics Authority (PSA), OCHA Philippines | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Philippines | ADM2 | cluster | National Mapping and Resource Information Authority (NAMRIA), Philippines Statistics Authority (PSA), OCHA Philippines | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Singapore | ADM0 | unit | Urban Redevelopment Authority, derived from ADM 3 | Open Data Commons Open Database License 1.0 |
| Hong Kong | ADM0 | unit | OpenStreetMap relation 913110 version 225 (2026-08-31T03:39:36Z) | Open Data Commons Open Database License 1.0 |
| Macau | ADM0 | unit | OpenStreetMap relation 1867188 version 114 (2026-07-09T18:39:26Z) | Open Data Commons Open Database License 1.0 |
| Japan | ADM1 | cluster candidate, not used | Prefecture governments, HDX | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| South Korea | ADM1 | cluster | OpenStreetMap relations 2297418 v150 (2026-10-12T22:50:31Z); 2396450 v83 (2026-06-28T10:44:02Z); 2395674 v58 (2026-06-28T10:44:02Z); 2297419 v117 (2026-06-30T04:26:06Z); 2349984 v54 (2026-07-04T15:44:26Z); 2395867 v47 (2026-06-28T10:44:02Z); 2349795 v54 (2026-06-28T10:44:02Z); 2306392 v227 (2026-07-07T02:13:57Z); 2308426 v104 (2026-10-19T14:43:04Z); 2327258 v83 (2026-08-10T14:29:18Z); 2327259 v110 (2026-08-27T09:42:54Z); 2355168 v75 (2026-08-27T09:42:54Z); 2304454 v147 (2026-08-10T14:29:18Z); 2393403 v113 (2026-06-28T10:44:02Z); 2398560 v45 (2026-06-28T10:44:02Z); 21039457 v7 (2026-10-31T08:06:16Z); 4162635 v20 (2026-06-28T10:44:02Z); 7348583 v24 (2026-06-28T10:44:02Z); 7348741 v17 (2026-06-28T10:44:02Z); 7348758 v19 (2026-06-28T10:44:02Z); 7348759 v18 (2026-06-28T10:44:02Z); 7816959 v15 (2026-06-28T10:44:02Z). Gwangju = union of its five districts; South Jeolla = Jeonnam-Gwangju minus Gwangju; Gunwi-gun moved from Daegu to North Gyeongsang | Open Data Commons Open Database License 1.0 |
| Mongolia | ADM1 | cluster | National Statistical Office of Mongolia, HDX | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Cambodia | ADM1 | cluster candidate, not used | Department of Geography of the Ministry of Land Management, Urbanization and Construction in 2008, WFP, HDX | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Indonesia | ADM1 | cluster | OCHA Regional Office for Asia and the Pacific (ROAP), HDX | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Laos | ADM1 | cluster | National Geographic Department of Laos | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Malaysia | ADM1 | cluster candidate, not used | UNHCR, HDX | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Thailand | ADM1 | cluster | Royal Thai Survey Department, HDX | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Timor-Leste | ADM1 | cluster | WHO, HDX | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |
| Vietnam | ADM1 | cluster | Government of Viet Nam, HDX | Creative Commons Attribution 3.0 Intergovernmental Organisations (CC BY 3.0 IGO) |

## ACAG PM2.5 V6.GL.03

Atmospheric Composition Analysis Group, Washington University in St. Louis. CC BY 4.0.

Shen, S., Li, C., van Donkelaar, A., Jacobs, N., Wang, C., & Martin, R. V. (2024). Enhancing global estimation of fine
particulate matter concentrations by including geophysical a priori information in deep learning. ACS ES&T Air, 1(5),
332–345. https://doi.org/10.1021/acsestair.3c00054

Adapted in `data/final/outcomes/pm25_annual.csv` and `pm25_monthly.csv.gz` as population-weighted district means.

## ACAG SatNO2 V4.GL.01

Atmospheric Composition Analysis Group, Washington University in St. Louis. CC BY 4.0. Zenodo record
https://doi.org/10.5281/zenodo.19740022.

Yan, Y., Shen, S., Zhang, Y., Li, C., Zhu, H., Chatterjee, D., Singh, I., & Martin, R. V. (2026). A global dataset of
surface NO2 estimation based on machine learning using process-based information. Scientific Data.
https://doi.org/10.1038/s41597-026-08329-2

Adapted in `data/final/outcomes/no2_annual.csv` and `no2_monthly.csv.gz` as population-weighted district means.

## Global Human Settlement Layer

European Commission, Joint Research Centre. CC BY 4.0.

Schiavina, M., Freire, S., & MacManus, K. (2023). GHS-POP R2023A - GHS population grid multitemporal (1975-2030).
European Commission, Joint Research Centre (JRC). https://doi.org/10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE

Schiavina, M., Melchiorri, M., & Pesaresi, M. (2023). GHS-SMOD R2023A - GHS settlement layers, application of the
Degree of Urbanisation methodology (stage I) to GHS-POP R2023A and GHS-BUILT-S R2023A, multitemporal (1975-2030).
European Commission, Joint Research Centre (JRC). https://doi.org/10.2905/A0DF7A6F-49DE-46EA-9BDE-563437A6E2BA

Pesaresi, M., & Politis, P. (2023). GHS-BUILT-S R2023A - GHS built-up surface grid, derived from Sentinel2 composite
and Landsat, multitemporal (1975-2030). European Commission, Joint Research Centre (JRC).
https://doi.org/10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA

GHS-POP and GHS-SMOD give the population weights and the urban centre variables in `data/final/`, and their files are
listed in `data/raw/ghsl/ghsl_sources.csv`. GHS-BUILT-S gives the 2015 built-up area (`built`) in
`data/final/covariates/light.csv`, and its file is listed in `data/raw/ntl/ntl_sources.csv`. None of the GHSL files
is redistributed here.

## TerraClimate

Climatology Lab, University of Idaho. Version 1.1, released under CC0 1.0.

Abatzoglou, J. T., Dobrowski, S. Z., Parks, S. A., & Hegewisch, K. C. (2018). TerraClimate, a high-resolution global
dataset of monthly climate and climatic water balance from 1958–2015. Scientific Data, 5, 170191.
https://doi.org/10.1038/sdata.2017.191

Annual district means of temperature, precipitation and wind speed are in `data/final/covariates/weather.csv`. The
grid files are not redistributed here.

## NASA FIRMS

We acknowledge the use of data from NASA's Fire Information for Resource Management System (FIRMS), part of NASA's
Earth Science Data and Information System (ESDIS). MODIS Collection 6.1 active fire detections (MCD14ML),
https://doi.org/10.5067/FIRMS/modis/MCD14ML. NASA open data are shared without restriction.

Giglio, L., Schroeder, W., & Justice, C. O. (2016). The collection 6 MODIS active fire detection algorithm and fire
products. Remote Sensing of Environment, 178, 31–41. https://doi.org/10.1016/j.rse.2016.02.054

Counts of fire detections around each district are in `data/final/covariates/fires.csv`. The yearly files used are
listed with URL and SHA-256 in `data/raw/firms/firms_sources.csv` and are not redistributed here.

## Harmonised night-time light

CC BY 4.0.

Li, X., Zhou, Y., Zhao, M., & Zhao, X. (2020). A harmonized global nighttime light dataset 1992–2018. Scientific
Data, 7, 168. https://doi.org/10.1038/s41597-020-0510-y

Li, X., Zhou, Y., Zhao, M., & Zhao, X. (2025). Harmonization of DMSP and VIIRS nighttime light data from 1992-2024 at
the global scale (Version 10) [Data set]. figshare. https://doi.org/10.6084/m9.figshare.9828827.v10

District means of night-time light (`ntl`) are in `data/final/covariates/light.csv`. The yearly files used are listed
with URL and SHA-256 in `data/raw/ntl/ntl_sources.csv` and are not redistributed here.

## World Bank income classifications

World Bank. (2024). World Bank country classifications by income level, historical (FY25 edition) [Data set].
https://ddh-openapi.worldbank.org/resources/DR0095334/download. CC BY 4.0.

`data/raw/worldbank/OGHIST.xlsx` is an unchanged copy.

## Japanese government copies (Public Data License 1.0)

Licence text https://www.digital.go.jp/resources/open_data/public_data_license_v1.0. The copies are unchanged.

| Files in `data/raw/designations/sources/` | Source | Terms of the site |
|---|---|---|
| `CAO_sdgs_*`, `CAO_supercity_*` | Cabinet Office, Japan, website, https://www.chisou.go.jp/ | https://www.chisou.go.jp/sousei/terms.html |
| `CAO_smartcity_*` | Cabinet Office, Japan, website, https://www8.cao.go.jp/cstp/ | https://www.cao.go.jp/notice/rule.html |
| `MLIT_*` | Ministry of Land, Infrastructure, Transport and Tourism website, https://www.mlit.go.jp/ | https://www.mlit.go.jp/link.html |
| `MIC_*` | Ministry of Internal Affairs and Communications website, https://www.soumu.go.jp/ | https://www.soumu.go.jp/menu_kyotsuu/policy/tyosaku.html |

The page each copy was taken from is given in `SDGs_SuperCity_sources_read_2026-11-01.txt` (Cabinet Office SDGs and
Super City files, MIC), `MLIT_sources_read_2026-11-01.txt` (MLIT and the Cabinet Office joint selection pages, whose
annex PDFs sit under https://www8.cao.go.jp/cstp/stmain/pdf/) and `scripts/designations/03_japan_sdgs_and_supercity.py`.

## Taiwanese government copies (Government Open Data License 1.0)

Licence declarations https://www.ey.gov.tw/Page/2EADDBFEDDB6357E and https://moda.gov.tw/announcement/publicdeclare/951.

| Files in `data/raw/designations/sources/taiwan_saved/` | Source |
|---|---|
| `ey_2019-11-13.html`, `ey_2020-07-22.html` | Executive Yuan, https://www.ey.gov.tw/ |
| `moda_smart_city_case_book_6.pdf` | Ministry of Digital Affairs, https://moda.gov.tw/ |

The page URL of each copy is given in `Taiwan_sources_read_2026-11-01.txt`. The `.txt` files with the same names
(`ey_2019-11-13.txt`, `ey_2020-07-22.txt`, `moda_smart_city_case_book_6.txt`) are text extracts made for this
project and are edited copies of the originals.
