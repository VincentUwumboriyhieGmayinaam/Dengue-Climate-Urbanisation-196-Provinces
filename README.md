# Urbanisation and delayed associations of temperature and rainfall with reported dengue in 196 provinces of six middle-income countries, 2010–22

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24204469.svg)](https://doi.org/10.5281/zenodo.24204469)

Code, derived data and results for a spatiotemporal modelling study of monthly reported dengue in 196 first-level administrative units (provinces, states and departments) of Brazil, Colombia, Indonesia, Nicaragua, Peru and Thailand, 2010–22.

## What the analysis does

* Links monthly reported dengue cases (OpenDengue v1.3) to province-level temperature and rainfall (NASA POWER, MERRA-2), the Oceanic Niño Index (NOAA) and GHSL R2023A built-up surface and population.
* Fits Poisson–lognormal mixed models (`glmmTMB`) with distributed lag non-linear cross-bases for temperature and rainfall (lags 0–6 months; `dlnm`), country seasonality with province-specific deviations, country-by-year effects, ONI, a BYM2 province effect (mixing parameter profiled by AIC), a log-population offset and a province-level latent AR(1) process.
* Confirms the primary model with a fully Bayesian INLA fit (negative binomial, BYM2 with the mixing parameter estimated, penalised complexity priors).
* Estimates within-province anomaly associations, effect modification by log built-up fraction, attributable cases against each province's climatological distribution, one-step-ahead residual diagnostics, out-of-sample skill (2021–22 withheld), 17 sensitivity analyses and 12 country models.

## Repository layout

| Path | Contents |
|---|---|
| `code/run_all.sh` | Runs the full analysis from the repository root (about 3–4 hours on two cores) |
| `code/data/01_opendengue_admin1_month.py` | OpenDengue subnational extract → province-month counts (weeks assigned to the month in which they start) |
| `code/data/02_power_fetch.py` | Re-downloads NASA POWER monthly climate for the sample points (cached results are in `data/raw/`) |
| `code/data/03_build_province_month.py` | Climate averaging, anomalies, name crosswalk to geoBoundaries, ONI merge → `data/P3_dengue_admin1_month_climate.csv` |
| `code/data/04_ghsl_zonal.R` | GHSL built-up surface and population by province (2010, 2015, 2020) |
| `code/R/01_prepare.R` | Eligibility (≥80% of months reported), cross-bases, adjacency graph |
| `code/R/09_fit_v2.R` | Primary, sensitivity and country models (options in the file header) |
| `code/R/10_attributable_v2.R` | Attributable cases (excess, deficit, net) |
| `code/R/11_skill.R` | Out-of-sample skill, 2021–22 |
| `code/R/12_onestep.R` | One-step-ahead quantile residuals, PIT, autocorrelation, Moran's I |
| `code/R/13_export_v2.R`, `18_supp_tables.R` | Curves, Table 2 and supplementary tables |
| `code/R/14_merge_ghsl.R` | Interpolates GHSL epochs to years and merges them with the province-month file |
| `code/R/15_urban_effect.R`, `16_tertile_effect.R` | Effect modification by built-up fraction |
| `code/R/17_bym2_matrix.R` | Scaled ICAR generalised inverse used for the BYM2 covariance |
| `code/R/19a_make_zerofill_data.py`, `19_zerofill_sensitivity.R` | Sensitivity analysis treating missing Colombian and Peruvian months as zero |
| `code/R/20_inla_bym2.R` | Confirmatory INLA model and urbanisation interaction |
| `code/python/` | Figures 1–7 and supplementary figures |
| `data/` | Analysis files, GHSL province summaries, province boundaries, name crosswalk, and raw NASA POWER and ONI inputs |
| `results/` | Tables, INLA output and figures as reported in the paper |

## Reproducing the results

```bash
git clone https://github.com/VincentUwumboriyhieGmayinaam/Dengue-Climate-Urbanisation-196-Provinces.git
cd Dengue-Climate-Urbanisation-196-Provinces
bash code/run_all.sh                 # models, tables and figures
Rscript code/R/20_inla_bym2.R        # optional: confirmatory INLA model (about 8 hours)
```

To rebuild the analysis file from the original sources, download the OpenDengue v1.3 spatial extract (`Spatial_extract_V1_3.csv`) into `data/raw/` and run `code/data/01_opendengue_admin1_month.py` and `code/data/03_build_province_month.py`; the GHSL rasters (R2023A, 1 km, Mollweide; BUILT_S and POP for 2010, 2015 and 2020) are needed only for `code/data/04_ghsl_zonal.R`, followed by `Rscript code/R/14_merge_ghsl.R data/P3_ghsl_province_epoch.csv`.

Software: R 4.4 with `data.table` 1.18, `dlnm` 2.4.10, `glmmTMB` 1.1.14 (TMB 1.9.19), `sf` 1.1, `spdep` 1.4, `MASS`; R-INLA 26.8.7 for the confirmatory model; Python 3 with `pandas`, `numpy`, `matplotlib` and `geopandas` (and `playwright` for rendering Figure 1). Random seeds are fixed in the scripts.

## Notes on the data

* Missing province-months are left missing in the primary analysis. OpenDengue records zero-case weeks explicitly for Brazil, Indonesia, Nicaragua and Thailand but not for Colombia and Peru, where a missing month most likely means zero reported cases; `19_zerofill_sensitivity.R` repeats the main models with those months set to zero (209 provinces).
* Case definitions differ between countries (probable, suspected and confirmed, or total notified cases), so levels are not compared between countries.

## Data sources

| Source | Use | Reference |
|---|---|---|
| OpenDengue v1.3 | Monthly reported dengue cases | Clarke J, et al. *Sci Data* 2024;11:296 |
| NASA POWER (MERRA-2) | Monthly temperature and rainfall | NASA Langley Research Center |
| NOAA Climate Prediction Center | Oceanic Niño Index | NOAA CPC |
| geoBoundaries | First-level boundaries | Runfola D, et al. *PLoS One* 2020;15:e0231866 |
| GHSL R2023A | Built-up surface and population | European Commission, Joint Research Centre, 2023 |

The derived files are redistributed for reproducibility; the terms of use of each original source apply, and users should cite the original sources.

## Licence

Code: MIT licence (see `LICENSE`). Derived data and results: CC BY 4.0, subject to the terms of the original data sources.

## Citation

Please cite the published article (citation will be added on publication). The code, data and results are archived at Zenodo: https://doi.org/10.5281/zenodo.24204469 (v1.0.0).
