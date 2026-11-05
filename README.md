# Urbanisation and delayed associations of temperature and rainfall with reported dengue in 196 provinces of six middle-income countries, 2010–22

Code, derived data and results for a spatiotemporal modelling study of monthly reported dengue in 196 first-level administrative units (provinces, states, departments) of Brazil, Colombia, Indonesia, Nicaragua, Peru and Thailand, 2010–22.

**Status:** manuscript in preparation (Draft 2, November 2026). Results may change before publication; please do not cite them until the paper is published.

## What the analysis does

* Links monthly reported dengue cases (OpenDengue v1.3) to province-level temperature and rainfall (NASA POWER, MERRA-2), the Oceanic Niño Index (NOAA), and GHSL built-up surface and population.
* Fits Poisson–lognormal mixed models (`glmmTMB`) with distributed lag non-linear cross-bases for temperature and rainfall (lags 0–6 months; `dlnm`), country and province-specific seasonality, country-by-year effects, ONI, a log-population offset and a province-level latent AR(1) process.
* Estimates within-province anomaly associations, effect modification by log built-up fraction (RQ3), attributable cases with a climatological-distribution counterfactual (RQ4), approximate one-step-ahead residual diagnostics, and out-of-sample skill (2021–22 withheld, CRPS).
* Includes 20 sensitivity and country analyses (see `code/run_all.sh`).

## Repository layout

| Path | Contents |
|---|---|
| `code/run_all.sh` | Runs the full analysis from the repository root (about 1–1.5 h on two cores) |
| `code/R/01_prepare.R` | Eligibility, cross-bases, adjacency graph → `out/p3_model_data.rds` |
| `code/R/02_fit_inla.R` | Prespecified INLA/BYM2 model (not run; INLA could not be installed in the analysis environment) |
| `code/R/09_fit_v2.R` | Primary and sensitivity models (options documented in the file header) |
| `code/R/10_attributable_v2.R` | Attributable cases (excess, deficit, net) |
| `code/R/11_skill.R` | Out-of-sample skill, 2021–22 |
| `code/R/12_onestep.R` | One-step-ahead quantile residuals, PIT, ACF, Moran's I |
| `code/R/13_export_v2.R` | Curves and summary tables |
| `code/R/14_merge_ghsl.R` | Interpolates GHSL epochs to years and merges with the province-month file |
| `code/R/15_urban_effect.R`, `16_tertile_effect.R` | Effect modification by built-up fraction |
| `code/python/` | Figures (maps, exposure–response, country curves, decision calendar, urbanisation) |
| `code/earth_engine/` | GHSL zonal statistics (R/terra and Python/rasterio versions) and the Earth Engine script |
| `data/P3_dengue_admin1_month_climate.csv` | Province-month cases, climate and ONI, 2009–23 (2009 supplies lags) |
| `data/P3_dengue_admin1_month_climate_pop_urban.csv` | As above, with interpolated population and built-up fraction |
| `data/P3_ghsl_province_epoch.csv` | GHSL built-up surface, land area and population by province, 2010/2015/2020 |
| `data/province_metrics.csv` | Province descriptive metrics used for the maps |
| `data/boundaries/` | Province boundaries (geoBoundaries ADM1, harmonised to OpenDengue units) |
| `results/tables/`, `results/figures/` | Model outputs and figures as reported in Draft 2 |

## Reproducing the results

```bash
git clone <this repository>
cd <repository>
bash code/run_all.sh
```

Software used: R 4.x with `data.table`, `dlnm`, `glmmTMB` 1.1.14 (with `TMB` 1.9.19), `sf`, `spdep`, `MASS`; Python 3 with `pandas`, `numpy`, `matplotlib`, `geopandas`; `terra` or `rasterio` for the GHSL extraction. The GHSL rasters (R2023A, 1 km, Mollweide) are not included because of their size; download them from the GHSL website and run `code/earth_engine/P3_ghsl_zonal_run_on_PC.R` to regenerate `data/P3_ghsl_province_epoch.csv`.

## Data sources

| Source | Use | Reference |
|---|---|---|
| OpenDengue v1.3 | Monthly reported dengue cases | Clarke J, et al. *Scientific Data* 2024 |
| NASA POWER (MERRA-2) | Monthly temperature, rainfall | NASA Langley Research Center |
| NOAA Climate Prediction Center | Oceanic Niño Index | NOAA CPC |
| geoBoundaries | ADM1 boundaries | Runfola D, et al. *PLoS One* 2020 |
| GHSL R2023A | Built-up surface and population | European Commission, Joint Research Centre, 2023 |

The derived files are redistributed for reproducibility; the original terms of use of each source apply, and users should cite the original sources.

## Licence

Code: MIT licence (see `LICENSE`). Derived data and results: CC BY 4.0, subject to the terms of the original data sources.

## Citation

Please cite the published article once available (citation and DOI to be added).
