# Analysis plan

The analysis plan cited in the paper as https://osf.io/86wbz. The answers carry the question numbers of the Secondary
Data Preregistration template (Weston et al., 2020, https://osf.io/x4gzt), published as van den Akker et al. (2021),
Meta-Psychology 5, https://doi.org/10.15626/MP.2020.2625. The plan was written on 1 and 2 Nov 2026, before any outcome
file was merged with the treatment table. On 4 Nov 2026 the author line and the later access dates in Q8 were filled
in. Supplement Table S7 of the paper lists the deviations from the plan.

---

## Part 1. Study information

### Q1 Working title

Smart city designation and urban air quality in East and Southeast Asia

### Q2 Authors

Jason Hung, Chulalongkorn University

### Q3 Research questions

RQ1. Does smart city designation reduce annual PM2.5 and nitrogen dioxide (NO2) concentrations in designated urban
districts, compared with undesignated urban districts in the same economy over the same years?

RQ2. Does designation increase night-time light in designated districts, and does PM2.5 decrease relative to night-time
light?

RQ3. Do the effects differ between programmes that support implementation, programmes that certify places, and
membership of the ASEAN Smart Cities Network, and how large are the effects in Japan, Thailand, Hong Kong and Singapore?

### Q4 Hypotheses

H1. Designation reduces NO2 more than PM2.5. NO2 comes mainly from local traffic and combustion, which smart mobility and
energy projects target, while a large share of PM2.5 in the region comes from other economies and from seasonal burning
of crops and forest.

H2. Designation increases night-time light, and the log of PM2.5 minus the log of night-time light decreases.

H3. Effects are largest for programmes that support implementation and smallest for network membership.

All tests are two-sided at the 5 percent level. RQ1 has two primary outcomes, PM2.5 and NO2, and their two p-values are
adjusted with the Holm method. H1 is supported when the NO2 effect is negative and significant after the Holm adjustment,
and the difference between the NO2 effect and the PM2.5 effect is negative with a 95 percent confidence interval that
excludes zero. The difference is estimated by a cluster bootstrap with 999 draws of first-level administrative units, in
which both outcomes are re-estimated on the same draw. When a primary effect is not significant, two one-sided tests
(TOST) at the 5 percent level check equivalence within plus or minus 5 percent, that is between ln 0.95 and ln 1.05 in
log points (Q20). H2 is supported when the night-time light effect is positive and the effect on the log ratio is
negative, each significant at the 5 percent level. H3 is supported when the reduction is largest for implementation
support and smallest for network membership, and a Wald test of equal effects across the three models, computed from the
bootstrap draws, rejects at the 5 percent level. H2 and H3 are secondary and their p-values are not adjusted.

---

## Part 2. Data description

### Q5 Datasets used

1. Smart city designation lists compiled for this study from official sources in 17 economies (Japan, South Korea,
   Taiwan, Hong Kong, Macau, Mongolia, Brunei, Cambodia, Indonesia, Laos, Malaysia, Myanmar, the Philippines, Singapore,
   Thailand, Timor-Leste and Vietnam). The lists cover the ASEAN Smart Cities Network (2018 onwards), Japan's MLIT Smart
   City Model Projects, SDGs Future Cities, Municipal SDGs Model Projects and Super City, Thailand's depa smart city
   certification, South Korea's national pilot smart cities and Smart Challenge, Indonesia's Movement Towards 100 Smart
   Cities, Malaysia's Smart City Framework pilots and smart city rating, Singapore's Smart Nation, Hong Kong's Smart City
   Blueprint, and, for checks only, Philippine Digital Cities 2025 and further Japanese, Korean and Malaysian rounds. One
   CSV per programme, 1,113 rows in all.
2. District boundaries. geoBoundaries gbOpen ADM1 and ADM2, commit 9469f09 (Philippines ADM3), and OpenStreetMap
   administrative relations for Hong Kong, Macau and South Korea.
3. GHS-POP R2023A, epoch 2015, 3 arc-seconds (population weights and size groups), and GHS-SMOD R2023A, epoch 2015
   (urban centres that define urban districts).
4. PM2.5 at ground level, Atmospheric Composition Analysis Group (ACAG) V6.GL.03, annual 1998 to 2024 and monthly 2005 to
   2024, 0.01 degree (Shen et al., 2024).
5. NO2 at ground level, ACAG SatNO2 V4.GL.01, monthly 2005 to 2024, 0.01 degree (Yan et al., 2026).
6. ERA5-Land monthly means (2 m temperature, total precipitation, 10 m wind components), 0.1 degree, 2005 to 2024.
7. NASA FIRMS MODIS Collection 6.1 standard fire detections, 2005 to 2024.
8. Earth Observation Group VIIRS Nighttime Lights V2.2, annual composites, 2012 to 2024, and the harmonised DMSP and
   VIIRS series of Li et al. (2020) for years before 2012.
9. Uncalibrated checks. MODIS MAIAC MCD19A2 aerosol optical depth (Collection 6.1) and OMI OMNO2d tropospheric NO2 column
   (Version 3).
10. GHS-BUILT-S R2023A (built-up area, synthetic control predictor) and the World Bank historical income classifications.

### Q6 Openness of the data

Every dataset is public and free. Items 1 to 5 and 10 need no account. ERA5-Land needs a free Copernicus Climate Data
Store account, FIRMS a free MAP_KEY, VIIRS a free Earth Observation Group account, and MAIAC and OMI a free NASA Earthdata
account. The ACAG products, GHS-POP and GHS-SMOD are released under CC BY 4.0. The designation lists are released with
this study.

### Q7 Access and persistent identifiers

- Designation lists, district units and treatment tables at
  https://github.com/newlivehung123123/smart_cities_sustainability (data/raw/designations, data/final).
- ACAG V6.GL.03 PM2.5 at https://satpmdata.s3.amazonaws.com/V6GL03/CNNPM25/ (global files, GL).
- ACAG SatNO2 V4.GL.01 at https://doi.org/10.5281/zenodo.19740022 (2005 to 2023) and
  https://satpmdata.s3.amazonaws.com/SATNO2V4GL01/ (2005 to 2024, the source used here).
- geoBoundaries at https://github.com/wmgeolab/geoBoundaries, commit 9469f09.
- GHS-POP and GHS-SMOD R2023A at https://human-settlement.emergency.copernicus.eu/download.php.
- ERA5-Land monthly at https://doi.org/10.24381/cds.68d2bb30.
- FIRMS at https://firms.modaps.eosdis.nasa.gov/.
- VIIRS VNL V2.2 at https://eogdata.mines.edu/products/vnl/, and Li et al. (2020) at https://doi.org/10.6084/m9.figshare.9828827.
- MAIAC MCD19A2 at https://doi.org/10.5067/MODIS/MCD19A2.061, and OMI OMNO2d at https://doi.org/10.5067/Aura/OMI/DATA3007.

### Q8 Date of access

Designation sources, boundaries, GHS-POP and GHS-SMOD were read on 1 November 2026. PM2.5 annual files and the NO2 and
PM2.5 monthly files were read on 1 November 2026. ERA5-Land, FIRMS, VIIRS, MAIAC and OMI
had not been accessed when the plan was written. FIRMS, TerraClimate (in place of ERA5-Land) and the harmonised
night-time light series of Li et al. (in place of VIIRS) were read on 3 November 2026. MAIAC and OMI were not used
(supplement Table S7).

### Q9 Data collection

Designation lists were compiled from ministry announcements, programme pages, official PDFs and press releases. Every row
records the source address, the date the source was read, the page or annex number and the name of the place as printed.
Each list is built by a script that checks the printed passage against a saved copy of the source. Satellite products
are produced by their authors from satellite retrievals and chemical transport models calibrated to ground monitors
(ACAG), or from satellite radiance (VIIRS, MAIAC, OMI). This study computes district means of every grid with fixed
weights (Q12).

### Q10 Codebooks

docs/codebook.md and docs/dataset_plan.md in the repository describe every column and coding rule. The treatment files
are fixed by these SHA-256 hashes, and any later change will be reported as a deviation.

| File | SHA-256 |
|---|---|
| data/final/designation_links.csv | cf28de4d295c0d2c0cf928eaea6895aa365d508cf871393609a3a568caceb3aa |
| data/final/treatment.csv | 485cc7ce0af6d74b4daeb659ffc44d5f309b53770f589e3d1858a1b5058e79db |
| data/final/units.csv | f81d4e4087ea3ca965c18571606b13b229ecadfd375324756f05892cacea2233 |
| data/raw/designations/link_pins.csv | f27a97bb7937761ffbfb402071ff4afc588ad0dce796627651e5330498cf7b95 |

---

## Part 3. Variables

### Q11 Manipulated variables

None. Designation is decided by governments and is observed.

### Q12 Measured variables

Treatment. D_it equals 1 from the first treated year of unit i and stays 1. The first treated year is the announcement
year when the announcement falls from January to June, and the next year otherwise. A designated city larger than one
district treats every district inside that city. A designated area smaller than one district treats the district that
contains it, and the link is flagged for a check that drops it. Each programme is coded implementation support (the
national government funds or runs projects in the selected places), certification (a label for places that meet stated
criteria), network membership (ASEAN Smart Cities Network) or whole-city strategy (Singapore, Hong Kong).

Outcomes.
- ln PM2.5, the log of the annual district mean of PM2.5 (micrograms per cubic metre).
- ln NO2, the log of the annual district mean of NO2 (parts per billion), where the annual mean is the mean of the 12
  monthly district means.
- ln NTL, the log of the annual district mean of VIIRS average-masked radiance, weighted by area.
- ln PM2.5 minus ln NTL.

District means. Each 0.01 degree cell is weighted by its GHS-POP 2015 population multiplied by the share of the cell
inside the district (exactextract). The area-weighted mean is kept as a check. Any unit-year mean at or below zero is set
missing and counted. The NO2 files store water and some shoreline cells as exactly 0 in place of a fill value. A cell
that is 0 in all 240 months from 2005 to 2024 is therefore treated as a cell with no data, and a cell that is 0 in only
some months is kept as a low estimate. Those partial zeros are estimates cut off at zero. They occur only from 2005 to
2016, mostly in rural Indonesia and Myanmar, and the same cells read 0.25 to 0.50 parts per billion in the same month of
neighbouring years. For each district and month the clipped share is the share of the population weight of cells with
data held by cells at 0. In the main specification the annual NO2 mean of a district is missing when the clipped share
is above 0.10 in any month of that year. At that share, cells whose true values are at most 0.5 parts per billion lower a
district mean of at least 1 part per billion by at most about 5 percent, the smallest effect of interest (Q20).

Covariates. Annual means of ERA5-Land 2 m temperature, total precipitation and 10 m wind speed (computed monthly from the
wind components), weighted by population in the same way, and ln(1 + count) of MODIS fire detections with confidence of
30 or more and type 0 (presumed vegetation fire) within 100 km and within 300 km of the district boundary. Districts with
no ERA5-Land land cell take the nearest land cell.

Other variables. 2015 population quartile among panel units (size group), first-level administrative unit (cluster),
economy, World Bank income group in the year of designation, and the GHS-BUILT-S 2015 built-up area.

### Q13 Unit of analysis and sample

The unit is the urban second-level administrative district (the Philippine city or municipality). A district is urban
if any part lies inside a GHS-SMOD 2015 urban centre. Non-administrative units (lakes, forests, reservoirs, unassigned
land) and one boundary fragment are excluded. Singapore, Hong Kong and Macau form one unit each and are not in the pooled
panel. Singapore and Hong Kong are used only in the synthetic control analyses, and Macau is not used.

The pooled panel has 2,256 districts in 328 first-level units across 14 economies, 2005 to 2024, at most 45,068
district-years after Malaysian district-years of 2024 are dropped (the 2023 rating round names only 4 of its 25 to 29
councils). In the main specification 619 districts are first treated from 2017 to 2024, by cohort 2017 (25), 2018
(235), 2019 (63), 2020 (49), 2021 (79), 2022 (70), 2023 (63) and 2024 (35). A further 21 districts first treated from
2025 to 2027 are untreated within the panel. By first programme model, 361 districts are implementation support
(including 33 Japanese districts whose first year has both a certification and an implementation support designation),
86 are certification and 172 are network membership. Taiwan, Mongolia and Timor-Leste have no treated district.

### Q14 Missing data

A district-period is missing when cells with data hold less than half of the district's population weight. Annual NO2 is
missing unless all 12 months are present, and in the main specification also when the clipped share is above 0.10 in any
month (Q12). Of the 45,068 panel district-years, NO2 is missing in 361 (20 districts) under the half-weight and 12-month
rules and in a further 109 (57 districts, all from 2005 to 2015) under the clipping rule. Eighteen districts, small
coastal and island districts where most of the population lives in cells with no NO2 data, have no NO2 value in any
year. Missing outcomes are not imputed. The estimator uses every observed district-year, and a check repeats the main
estimate on districts observed in every year. Treated district-years that the estimator cannot impute (Q23) are dropped
and counted.

### Q15 Outliers

No observation is removed beyond the missing-data rules in Q14. Outcomes are in logs. The area-weighted mean is a check
on the influence of single populous cells. Annual district means of NO2 run from 0.31 to 33.26 parts per billion in the
main specification, and 13 district-years, all in Indonesia from 2006 to 2015, are below 0.5. With every district-year
kept (Q24) the lowest is 0.003 and 58 district-years are below 0.5.

### Q16 Sampling weights

Regressions are unweighted, so each district counts equally. A check weights each district by its 2015 population.

---

## Part 4. Knowledge of data

### Q17 Prior publications using these data

Studies of Chinese smart city pilots, for example Cui and Cao (2022), estimate PM2.5 effects for mainland China, which is
not in this sample.

### Q18 Prior knowledge of the data

The designation lists, district boundaries, urban centres and 2015 population were compiled and inspected in full,
including the number of treated districts by economy, cohort and programme model reported in Q13. The district means of
annual PM2.5 (1998 to 2024), monthly PM2.5 (2005 to 2024) and monthly NO2 (2005 to 2024) were computed before
registration. The extraction logs printed, for each period, the number of districts with missing data, the number of
negative cells and the median district mean across all districts (for example 17.15 micrograms per cubic metre of
annual PM2.5 in 2011 and 19.19 in 2015). A first NO2 extraction counted the cells stored as exactly 0 as clean air, and
one coastal district, Cavite City in the Philippines, came out at 0.075 parts per billion. The cell values showed the
cause. Cells that are 0 in every month from 2005 to 2024 lie on water and shorelines, while other cells reach 0 only in
some months of 2005 to 2016 and read a few tenths of a part per billion in the same month of neighbouring years. The NO2
uncertainty layer is proportional to the value (0.455 times the value) and cannot separate the two kinds of zero. This
led to the zero rule and the clipping rule in Q12, and NO2 was extracted again under those rules. The zero rule was fixed
from cell values alone. The 0.10 threshold of the clipping rule was set after the distribution of the clipped share
across all districts and years had been printed, and follows from the arithmetic in Q12 and the smallest effect of
interest in Q20. To report what the two rules cost, the unit identifiers of the affected districts were matched with the
treatment table, with no outcome value in the match. Three of the 18 districts with no NO2 in any year are treated in
the main specification (Gwangyang 2020, Kota Baubau 2021 and Son Tra 2018), and 13 of the 57 districts that lose a year
under the clipping rule are treated, all in Indonesia and first treated from 2017 to 2023. No outcome has been compared
between designated and undesignated districts, no outcome value has been merged with the treatment table, and no
regression of any kind has been run. Published results for Chinese pilots (about 5.3 percent lower PM2.5 in Cui and Cao, 2022) informed the
smallest effect of interest.

---

## Part 5. Analyses

### Q19 Statistical models

Main estimator for RQ1 and RQ2. The imputation estimator of Borusyak, Jaravel and Spiess (2024).

ln Y_it = α_i + λ_c(i)t + μ_s(i)t + X_it′β + τ_it D_it + ε_it

α_i is the district fixed effect, λ_c(i)t the economy-by-year fixed effect, μ_s(i)t the size-group-by-year fixed effect
and X_it the covariates of Q12. The model is fitted on untreated district-years only, the fitted model predicts the
untreated outcome of every treated district-year, and τ_it is the observed minus the predicted outcome. The headline effect is the mean of
τ_it over treated district-years 0 to 5 years after the first treated year, each district-year weighted equally. The
mean over all treated district-years is a check. Standard errors use the conservative variance estimator of Borusyak,
Jaravel and Spiess (2024), clustered by first-level administrative unit.

Event study. Effects for each year from 0 to 5 years after designation, and the Borusyak, Jaravel and Spiess test of
eight pre-designation indicators (years minus 8 to minus 1) on untreated district-years. The method of Rambachan and Roth
(2023), with the relative magnitudes restriction, reports the breakdown value for the headline effect. Because the bounds
need pre- and post-designation coefficients from one regression, they use the Sun and Abraham (2021) event study with
year minus 1 as the reference and its clustered covariance matrix.

RQ2. The same estimator with ln NTL and ln PM2.5 minus ln NTL as outcomes, 2012 to 2024, so every treated district has
at least five pre-designation years. The Li et al. (2020) series extends the night-time light estimate to 2005 as a
check.

RQ3. A separate sample for each programme model. Each sample keeps the districts whose first designation falls under that
model as treated, keeps never-designated districts, and keeps districts first designated under another model only until
the year before that designation. Districts whose first year has both certification and implementation support count as
implementation support, and a check drops them. A check also drops district-years after a later designation under a
different model. Effects for Japan and Thailand are means of τ_it over the treated district-years of each economy from the
pooled estimate. A split by World Bank income group in the year of designation gives a further comparison. Differences
between models are tested by a Wald test on the bootstrap draws of Q4. Super City is certification in the main
specification, and a check codes it implementation support.

Singapore and Hong Kong. Augmented synthetic control (ridge, Ben-Michael, Feller and Rothstein, 2021) and synthetic
difference-in-differences (Arkhangelsky et al., 2021) for each city-state and each outcome. Singapore is first treated in
2015 (Smart Nation, 24 November 2014) and Hong Kong in 2018 (Smart City Blueprint, 15 December 2017). PM2.5
pre-designation years are 1998 to 2014 for Singapore and 1998 to 2017 for Hong Kong, and NO2 pre-designation years begin
in 2005. Donors are the 1,576 urban districts with no designation under any specification by 2024. Predictors are the
outcome in every pre-designation year, 2015 population, 2015 built-up area, pre-designation night-time light and weather.
Inference assigns designation to every donor in turn and ranks the ratio of post- to pre-designation root mean squared
prediction error. A second placebo moves the designation five years earlier and uses only years before the true
designation. The Singapore check uses monthly PM2.5 and NO2, excludes August to October in every year (the regional
burning season) and adds fire detections within 500 km as a predictor. The Hong Kong check dates designation by the 2015
Kowloon East pilot (first treated 2015). A within-Hong Kong check compares Kwun Tong district (Kowloon Bay and Kwun Tong
business areas of the pilot) with the other 17 districts by synthetic control and assigns the pilot to each district in
turn, so the smallest attainable p-value is 1/18. A further check adds Kowloon City district (Kai Tak Development) as a
second treated district.

China replication (supplement). The same estimator applied to the 2012 to 2014 Chinese national smart city pilots at
prefecture level, to check whether these data and this estimator recover an effect of the published size.

### Q20 Effect size of interest

The smallest effect of interest is a 5 percent change in PM2.5 or NO2 (between ln 0.95 and ln 1.05), close to the 5.3
percent reduction reported for Chinese pilot cities by Cui and Cao (2022).

### Q21 Statistical power

Before any effect is estimated, the minimum detectable effect is computed for each primary outcome from 500 placebo
designations among never-designated districts. Each placebo selects, within each economy, the same number of districts as
are treated there and assigns them the observed first treated years of that economy, and the main estimator is run on the
placebo. The minimum detectable effect at 80 percent power and 5 percent significance (two-sided) is 2.80 times the
standard deviation of the 500 placebo estimates. The paper also reports 2.80 times the standard error of the actual
estimate. If the minimum detectable effect exceeds 5 percent, the paper states that the study cannot detect the
smallest effect of interest and interprets a non-significant result by its confidence interval and the TOST result
only.

### Q22 Inference criteria

Primary effects are significant when the Holm-adjusted two-sided p-value is below 0.05. A primary effect is equivalent to
zero when both one-sided tests reject at 0.05, that is when the 90 percent confidence interval lies between ln 0.95 and
ln 1.05. Secondary effects (H2, H3, focal economies) use unadjusted two-sided p-values at 0.05 and are reported as
secondary. Synthetic control effects are significant when the placebo p-value is 0.05 or below. Estimates that rely on
fewer than 30 clusters use wild cluster bootstrap p-values (Webb weights, 9,999 draws).

### Q23 Violations of assumptions and estimation problems

If the pre-designation test rejects at 0.05, the main specification is kept, and the paper reports the Rambachan and Roth
bounds and the Callaway and Sant'Anna (2021) estimate with pre-designation covariates next to the main estimate. Treated
district-years without an untreated district in the same economy, year and size group, or without enough untreated years
for the district fixed effect, cannot be imputed. These district-years are dropped and their number is reported. Fixed
effects are estimated by alternating projections with a tolerance of 1e-10. If a synthetic control fits the
pre-designation years poorly, the paper reports the pre-designation error and relies on the synthetic
difference-in-differences estimate and the placebo ranks. Any change to this plan is reported in a deviations table with
its reason.

### Q24 Reliability and robustness

Every check is reported in the supplement. No check replaces the main estimate. A conclusion is called robust when every
check gives an estimate of the same sign as the main estimate, and every check that changes the sign or the significance
is named in the main text.

Estimators. Callaway and Sant'Anna (2021, doubly robust, not-yet-treated comparisons), Sun and Abraham (2021), stacked
difference-in-differences (Cengiz et al., 2019), de Chaisemartin and D'Haultfœuille (2020), and two-way fixed effects with
the Goodman-Bacon (2021) decomposition. An entropy-balanced comparison group matched on pre-designation outcomes and 2015
population.

Measurement. MAIAC aerosol optical depth and OMI NO2 columns, which do not use ground monitors. Area-weighted means. NO2
with every district-year kept, including those above the 0.10 clipped share (Q12).

Rival explanations. Dropping 2020 and 2021 (COVID-19). Monthly outcomes that exclude the burning months, February to
April in Cambodia, Laos, Myanmar, Thailand and Vietnam, and August to October in Indonesia, Malaysia, Singapore and Brunei.
Dropping undesignated districts that border a designated district or share its urban centre, and estimating effects in
bordering districts (spillovers). Treating the year before designation as treated (anticipation). Dropping one economy at
a time, dropping Indonesia, and dropping capital cities. GHSL urban centres as the unit. Randomisation inference with
1,000 permutations of designation dates within each economy. Conley standard errors with 100 km and 250 km cut-offs, and
a wild cluster bootstrap with economies as clusters.

Coding checks. Dropping part-area links. Indonesia's 2023 round coded 2022, and Indonesian places on the MoU list only
dropped. Dropping Vietnam's undesignated districts from the comparison group. Taiwan excluded from the synthetic control
donors. Dropping undesignated districts in a prefecture or province named by a prefecture-only designation (257 districts).
The urban districts where at least half of the 2015 population lives in an urban centre. The four other Japanese
joint-selection programmes, the Digital Garden Health Special Zones, the Korean campus challenge and 2019 theme complexes,
Malaysia's 2023 rating with its four named councils, and the Philippine Digital Cities (coded treated, and dropped from
the comparison group). Unweighted and population-weighted regressions (Q16), and the balanced panel (Q14).

### Q25 Exploratory analyses

Effects by 2015 size group, effects beyond five years after designation, effects by month of the year for NO2, and
effects of part-area designations compared with whole-district designations. These are labelled exploratory in the paper.

---

## Part 6. Statement of integrity

The author confirms that the information in this registration is accurate and complete to the best of the author's
knowledge, that the data were accessed and examined only as described in Q8 and Q18, and that no analysis relating
designation to any outcome was conducted before the registration was submitted.

---

## References

Arkhangelsky, D., Athey, S., Hirshberg, D. A., Imbens, G. W., & Wager, S. (2021). Synthetic difference-in-differences.
American Economic Review, 111(12), 4088–4118.

Ben-Michael, E., Feller, A., & Rothstein, J. (2021). The augmented synthetic control method. Journal of the American
Statistical Association, 116(536), 1789–1803.

Borusyak, K., Jaravel, X., & Spiess, J. (2024). Revisiting event-study designs: Robust and efficient estimation. Review of
Economic Studies, 91(6), 3253–3285.

Callaway, B., & Sant'Anna, P. H. C. (2021). Difference-in-differences with multiple time periods. Journal of
Econometrics, 225(2), 200–230.

Cengiz, D., Dube, A., Lindner, A., & Zipperer, B. (2019). The effect of minimum wages on low-wage jobs. Quarterly Journal
of Economics, 134(3), 1405–1454.

Cui, H.-Y., & Cao, Y.-Q. (2022). Do smart cities have lower particulate matter 2.5 (PM2.5)? Evidence from China.
Sustainable Cities and Society, 86, 104082. https://doi.org/10.1016/j.scs.2022.104082

de Chaisemartin, C., & D'Haultfœuille, X. (2020). Two-way fixed effects estimators with heterogeneous treatment effects.
American Economic Review, 110(9), 2964–2996.

Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing. Journal of Econometrics, 225(2),
254–277.

Li, X., Zhou, Y., Zhao, M., & Zhao, X. (2020). A harmonized global nighttime light dataset 1992–2018. Scientific Data, 7,
168.

Rambachan, A., & Roth, J. (2023). A more credible approach to parallel trends. Review of Economic Studies, 90(5),
2555–2591.

Shen, S., Li, C., van Donkelaar, A., Jacobs, N., Wang, C., & Martin, R. V. (2024). Enhancing global estimation of fine
particulate matter concentrations by including geophysical a priori information in deep learning. ACS ES&T Air, 1(5),
332–345. https://doi.org/10.1021/acsestair.3c00054

Sun, L., & Abraham, S. (2021). Estimating dynamic treatment effects in event studies with heterogeneous treatment
effects. Journal of Econometrics, 225(2), 175–199.

van den Akker, O. R., Weston, S., Campbell, L., Chopik, B., Damian, R., Davis-Kean, P., Hall, A., Kosie, J., Kruse, E.,
Olsen, J., Ritchie, S., Valentine, K. D., van 't Veer, A., & Bakker, M. (2021). Preregistration of secondary data
analysis: A template and tutorial. Meta-Psychology, 5. https://doi.org/10.15626/MP.2020.2625

Yan, Y., Shen, S., Zhang, Y., Li, C., Zhu, H., Chatterjee, D., Singh, I., & Martin, R. V. (2026). A global dataset of
surface NO2 estimation based on machine learning using process-based information. Scientific Data.
https://doi.org/10.1038/s41597-026-08329-2
