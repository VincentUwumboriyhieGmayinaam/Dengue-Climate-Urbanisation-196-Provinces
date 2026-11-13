#!/usr/bin/env bash
# Reproduce the analysis from the repository root:  bash code/run_all.sh
# Requires R >= 4.3 (data.table, dlnm, glmmTMB, sf, spdep, MASS) and Python 3 (pandas, numpy, matplotlib, geopandas, playwright
# for Figure 1). About 3-4 hours on two cores. The confirmatory INLA model (code/R/20_inla_bym2.R) is run separately (about 8 hours).
# Data construction (code/data/01-04) is optional: its outputs are included in data/.
set -euo pipefail
cd "$(dirname "$0")/.."; mkdir -p out
R="Rscript"; f() { $R code/R/09_fit_v2.R "$@"; }

$R code/R/01_prepare.R                    # analytic data, cross-bases, adjacency graph
$R code/R/17_bym2_matrix.R                # scaled ICAR generalised inverse for the BYM2 covariance

# BYM2 mixing parameter profiled by AIC; unstructured province effect (phi = 0) as comparison
f iid
for p in 0.2 0.5 0.75 0.9 0.99; do f bym2_$p bym2=$p; done

# primary and sensitivity models with BYM2 (phi = 0.9)
export P3_BYM2=0.9
f primary
f noONI noONI=1; f drop1516 drop_years=2015,2016; f drop2021 drop_years=2020,2021
f harm3 harm=3; f rainlog rainlog=1; f lag9 lag=9; f lagdf4 lagdf=4; f ctrymonth ctrymonth=1
f trend offset=0
f noBRA subset=COL,IDN,NIC,PER,THA
for c in COL IDN NIC PER THA; do f jk_$c subset=$(echo BRA COL IDN NIC PER THA | tr ' ' '\n' | grep -v $c | paste -sd,); done
f anomaly anomaly=1
f hold_clim holdout=1; f hold_noclim holdout=1 noclimate=1
f urban urban=1; f urbanraw urban=1 urbanraw=1; f urbtert urbtert=1

# country models (country knots and centring; unstructured province effect)
unset P3_BYM2
for c in BRA COL IDN NIC PER THA; do f ck_$c subset=$c cknots=1; f an_$c subset=$c anomaly=1; done
export P3_BYM2=0.9

# post-processing
$R code/R/10_attributable_v2.R; $R code/R/11_skill.R
$R code/R/12_onestep.R out/v2_primary.rds; $R code/R/12_onestep.R out/v2_ctrymonth.rds
$R code/R/15_urban_effect.R out/v2_urban.rds; $R code/R/15_urban_effect.R out/v2_urbanraw.rds; $R code/R/16_tertile_effect.R
$R code/R/13_export_v2.R; $R code/R/18_supp_tables.R

# sensitivity: missing Colombian and Peruvian months as zero (209 provinces)
python3 code/R/19a_make_zerofill_data.py zerofill
mkdir -p zerofill/data/boundaries zerofill/out; cp data/boundaries/P3_provinces_ADM1_shapefile.zip zerofill/data/boundaries/
( cd zerofill && export P3_N_PROV=209 && $R ../code/R/01_prepare.R && $R ../code/R/17_bym2_matrix.R &&
  $R ../code/R/09_fit_v2.R primary && $R ../code/R/09_fit_v2.R anomaly anomaly=1 && $R ../code/R/09_fit_v2.R urban urban=1 )
$R code/R/19_zerofill_sensitivity.R zerofill

# figures
python3 code/python/province_metrics.py
for p in fig2_data_at_a_glance fig3_spatial_patterns fig4_exposure_response fig5_urbanisation fig6_country_curves fig7_decision_calendar figS_supplementary; do
  python3 code/python/$p.py; done
python3 code/python/fig1_conceptual_framework.py && python3 code/python/fig1_render.py 2 out/Figure1_conceptual_framework.png --pdf
