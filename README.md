# Smart city designation and urban air quality in East and Southeast Asia

Data and code for a study of whether national smart city designation lowers fine particulate matter (PM2.5) and
nitrogen dioxide (NO2) in the designated urban districts of 17 East and Southeast Asian economies. The pooled panel
has 2,256 urban districts in 14 economies from 2005 to 2024, of which 619 are first designated from 2017 to 2024.
Effects are estimated with the imputation estimator of Borusyak, Jaravel and Spiess (2024). Singapore and Hong Kong,
each one unit, are estimated by augmented synthetic control and synthetic difference-in-differences.

Author: Jason Hung, Chulalongkorn University.

## Analysis plan

The analysis plan cited in the paper as https://osf.io/86wbz is `docs/osf_registration.md`. The scripts refer to its
questions as Q1 to Q25. Supplement Table S7 of the paper lists the deviations from the plan.

## Folders

| Folder | Holds |
|---|---|
| `data/raw/designations/` | One CSV per designation programme, every row with its source URL, page and date read, and `link_pins.csv` (hand pins for places that cannot be matched by name) |
| `data/raw/designations/sources/` | Saved copies of the pages and PDFs the lists were read from, and the `*_sources_read_*.txt` notes that quote the passage behind each coding decision. Only copies whose terms allow redistribution are included (`docs/source_files.csv`) |
| `data/raw/boundaries/` | Records of every boundary file used (`boundary_sources.csv`, `cluster_sources.csv`) with URL and SHA-256, geoBoundaries metadata, saved OpenStreetMap relations and Nominatim answers, and Japanese unit names filled from OpenStreetMap |
| `data/raw/ghsl/` | Record of the GHS-SMOD and GHS-POP R2023A files used |
| `data/raw/firms/`, `data/raw/ntl/` | Records of the FIRMS fire files and the night-time light and GHS-BUILT-S files used, with URL and SHA-256 |
| `data/raw/worldbank/` | `OGHIST.xlsx`, the World Bank historical income classifications |
| `data/final/` | `units.csv` (7,163 district units), `designation_links.csv` (2,967 links of designation rows to units), `treatment.csv` (first treated year of every unit under each specification) |
| `data/final/outcomes/` | District means of PM2.5 (annual 1998 to 2024, monthly 2005 to 2024) and NO2 (monthly and annual 2005 to 2024) |
| `data/final/covariates/` | Weather (`weather.csv`), fire counts (`fires.csv`), night-time light and 2015 built-up area (`light.csv`) for every panel district and city-state |
| `outputs/analysis/` | The analysis panel (`panel.parquet`, `panel_log.json`) and every estimate the paper reports, one CSV per script and part |
| `exhibits/` | Tables I to III, Figures 1 to 3, supplement Tables S1 and S2 and supplement Figure S1 of the paper |
| `scripts/` | Python scripts, numbered in the order they run within each folder |
| `docs/` | `codebook.md` (every column of `data/final/`), `dataset_plan.md` (coding rules and decisions), `osf_registration.md` (the analysis plan), `data_licences.md`, `source_files.csv` |

`data/interim/` (2.7 GB) and the raw covariate grids are not in the repository. The scripts below rebuild them.

## Licences

Code in `scripts/` is under the MIT License. Documentation and the designation lists are under CC BY 4.0. The files in
`data/final/` and the OpenStreetMap material in `data/raw/boundaries/` are under the Open Database License 1.0, because
the units are OpenStreetMap boundaries in Japan, South Korea, Taiwan, Hong Kong and Macau. `LICENSE.md` sets out which
licence covers which file, and `NOTICE.md` gives the credit line of every data source. `docs/data_licences.md` records
how the terms of each source were checked.

## Environment

Python 3.13.5 with the packages in `requirements.txt`. h5py must include the ros3 driver, which the Anaconda build has.
Every script takes its folders as arguments and is run from the repository root with `python -I`. Downloads go to an
empty folder outside the repository, written below as `$DL`. No R or Stata is used. The analysis scripts were run
with `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`, because they run their
own worker processes.

## Rebuilding the dataset

### 1. Designation lists

Scripts 02, 03 and 09 in `scripts/designations/` run on the files in this repository and reproduce its CSVs byte for
byte.

```bash
python -I scripts/designations/02_mlit2020_and_joint_selection.py data/raw/designations data/raw/designations/sources
```

```bash
python -I scripts/designations/03_japan_sdgs_and_supercity.py data/raw/designations data/raw/designations/sources
```

```bash
python -I scripts/designations/09_taiwan.py data/raw/designations data/raw/designations/sources
```

The other scripts read saved copies that cannot be redistributed. `docs/source_files.csv` gives the path and SHA-256 of
each, and its URL is in the designation CSVs and the notes. Web pages may have changed since they were read on 1 Nov
2026. The coded lists and the quoted passages are in the repository.

### 2. District units

```bash
python -I scripts/units/01_boundaries.py data/raw/boundaries data/interim/units "$DL"
```

```bash
python -I scripts/units/01b_clusters.py data/raw/boundaries data/interim/units "$DL"
```

```bash
python -I scripts/units/02_urban_centres.py data/raw/ghsl data/interim/units "$DL"
```

```bash
python -I scripts/units/03_units.py data/interim/units data/raw/boundaries/boundary_sources.csv
```

```bash
python -I scripts/units/04_population.py data/interim/units data/raw/ghsl data/interim data/final "$DL"
```

```bash
python -I scripts/units/05_jpn_names.py data/interim/units data/raw/boundaries
```

```bash
python -I scripts/units/06_flags.py data/final/units.csv
```

Boundary files come from geoBoundaries commit 9469f09 and are checked against the SHA-256 in the two records.
OpenStreetMap relations and Nominatim answers already saved in `data/raw/boundaries/` are reused, so no request is sent
for them. `04_population.py` downloads the GHS-POP 2015 tiles that meet an urban unit (about 135 MB each) and writes
`data/interim/ghs_pop_2015_001deg.tif`.

### 3. Treatment

```bash
python -I scripts/treatment/02_pins.py data/raw/designations/link_pins.csv data/interim/units data/raw/boundaries data/interim/treatment
```

```bash
python -I scripts/treatment/01_link.py data/raw/designations data/final/units.csv data/raw/boundaries/jpn_name_fill.csv data/interim/treatment/pins_resolved.csv data/interim/treatment
```

```bash
python -I scripts/treatment/03_check_links.py data/raw/designations data/interim/treatment/links.csv data/interim/units data/raw/boundaries
```

```bash
python -I scripts/treatment/04_treatment.py data/raw/designations data/interim/treatment/links.csv data/final/units.csv data/final
```

`02_pins.py` runs before `01_link.py`, because the links use the resolved pins. `03_check_links.py` compares a sample of
the links made by name with geography and writes a check file only.

### 4. Outcomes

```bash
python -I scripts/outcomes/01_weights.py data/interim/units/units.parquet data/final/units.csv data/interim/ghs_pop_2015_001deg.tif data/interim/outcomes
```

```bash
python -I scripts/outcomes/02_extract.py pm25_annual data/interim/outcomes/weights.parquet data/interim/outcomes
```

```bash
python -I scripts/outcomes/02_extract.py pm25_monthly data/interim/outcomes/weights.parquet data/interim/outcomes
```

```bash
python -I scripts/outcomes/02_extract.py no2_monthly data/interim/outcomes/weights.parquet data/interim/outcomes
```

```bash
python -I scripts/outcomes/03_combine.py data/interim/outcomes data/final/outcomes
```

The PM2.5 and NO2 files are read from the public ACAG bucket on Amazon S3 and are never stored. Only the chunks that hold
a cell of a panel unit or city-state are downloaded. A stopped run resumes from the last finished period. The NO2 step
first saves the monthly cell values (about 1.8 GB in `data/interim/outcomes/no2_cells/`), because the rule for cells
stored as zero needs all 240 months.

### 5. Covariates

```bash
python -I scripts/covariates/01_weather.py data/interim/outcomes/weights.parquet data/raw/terraclimate data/final/covariates
```

```bash
python -I scripts/covariates/02_fires.py data/interim/units/units.parquet data/interim/outcomes/weights.parquet data/raw/firms data/final/covariates
```

```bash
python -I scripts/covariates/03_light_built.py data/interim/outcomes/weights.parquet data/raw/ntl data/final/covariates
```

Weather comes from TerraClimate, fire counts from the MODIS active fire archive of NASA FIRMS, night-time light from
the harmonised series of Li et al. and built-up area from GHS-BUILT-S R2023A. None of these needs an account. Each
script downloads its files again and keeps only the cells or detections in the study region.

### 6. Design exhibits

```bash
python -I scripts/exhibits/01_design_exhibits.py data/final data/interim/units/units.parquet exhibits
```

Writes Table I (programmes and designated districts by economy), supplement Table S1 (data sources), Figure 1 (map of
designation status) and supplement Figure S1 (first designations by year and programme model) to `exhibits/tables/`
and `exhibits/figures/`. The script reads the treatment table and the unit boundaries only, never an outcome.

## Analysis

The analysis scripts are in `scripts/analysis/` and run in this order.

```bash
python -I scripts/analysis/01_panel.py data/final outputs/analysis
```

```bash
python -I scripts/analysis/02_mde.py outputs/analysis share
```

```bash
python -I scripts/analysis/03_estimate.py outputs/analysis
```

```bash
python -I scripts/analysis/04_synth.py outputs/analysis data/final 8
```

```bash
python -I scripts/analysis/05_robust.py outputs/analysis data/final estimators
```

`05_robust.py` is run six times, with the last argument `estimators`, `rival`, `coding`, `inference`, `honest` and
`extras` in turn.

```bash
python -I scripts/analysis/06_trends.py outputs/analysis
```

```bash
python -I scripts/analysis/07_ntl_ceiling.py outputs/analysis
```

```bash
python -I scripts/analysis/08_ri_cluster.py outputs/analysis 1000 4
```

```bash
python -I scripts/exhibits/02_results_exhibits.py outputs/analysis exhibits
```

`01_panel.py` joins the outcomes and covariates to the treatment table and writes the analysis panel. `02_mde.py`
gives the minimum detectable effect from placebo designations among never-designated districts (plan Q21).
`03_estimate.py` gives the pooled estimates for RQ1 to RQ3, the pre-trend test, H1 and the Japanese and Thai estimates.
`04_synth.py` gives the Singapore and Hong Kong estimates and their checks, and the last argument is the number of
processes for the placebo runs. `05_robust.py` gives the robustness checks of the plan and of the deviations in
supplement Table S7. `06_trends.py`, `07_ntl_ceiling.py` and `08_ri_cluster.py` are exploratory checks outside the plan.
`02_results_exhibits.py` writes Tables II and III, Figures 2 and 3 and supplement Table S2.

Covariates are read from every CSV in `data/final/covariates/`, one row per unit and year, with the columns `unit_id`,
`year` and one column per covariate. The main specification uses `t2m`, `tp`, `wind10`, `ln_fire_100km` and
`ln_fire_300km`. The synthetic control also uses `ntl`, `built` (2015) and `ln_fire_500km`. The within-Hong Kong check
reads `data/final/outcomes/hk_districts_annual.csv` (`district`, `year`, `pm25`, `no2`, `max_clip_share`). That file was
not built, so the check is skipped.

The estimators are checked on simulated panels only, without reading any file in `data/`.

```bash
python -I scripts/analysis/test_did.py 200
```

```bash
python -I scripts/analysis/test_synth.py 100
```

```bash
python -I scripts/analysis/test_honest.py
```

`test_did.py` checks the imputation estimator, its conservative standard errors, the pre-trend test, the cluster and
wild bootstraps, the Wald test of equal effects, Holm and TOST. `test_synth.py` checks the synthetic control weights,
the ridge penalty, recovery of a known effect by each of the three methods, residualising on covariates, the placebo
ranks and the in-time placebo. `test_honest.py` checks the bounds on violations of parallel trends in `honest.py`.

## Status

The dataset, the covariates, the analysis and the exhibits are complete. The manuscript is not in the repository. The
plan and the record of each step are in `docs/dataset_plan.md`.
