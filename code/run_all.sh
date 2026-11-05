#!/usr/bin/env bash
# Reproduce all Paper 3 results from the repository root:  bash code/run_all.sh
# Requires R (data.table, dlnm, glmmTMB, sf, spdep, MASS) and Python 3 (pandas, numpy, matplotlib, geopandas).
# Total run time about 1–1.5 hours on two cores.
set -euo pipefail
cd "$(dirname "$0")/.."; mkdir -p out
R="Rscript"; f() { $R code/R/09_fit_v2.R "$@"; }
$R code/R/01_prepare.R                                         # analytic data, cross-bases, adjacency graph (uses population/built-up file)
f primary                                                     # primary model (population offset)
f noONI noONI=1; f drop1516 drop_years=2015,2016; f drop2021 drop_years=2020,2021
f harm3 harm=3; f rainlog rainlog=1; f lag9 lag=9; f lagdf4 lagdf=4; f ctrymonth ctrymonth=1
f trend offset=0                                              # province trend in place of the offset
f noBRA subset=COL,IDN,NIC,PER,THA
for c in COL IDN NIC PER THA; do f jk_$c subset=$(echo BRA COL IDN NIC PER THA | tr ' ' '\n' | grep -v $c | paste -sd,); done
f anomaly anomaly=1
for c in BRA COL IDN NIC PER THA; do f ck_$c subset=$c cknots=1; f an_$c subset=$c anomaly=1; done
f hold_clim holdout=1; f hold_noclim holdout=1 noclimate=1
f urban urban=1; f urbanraw urban=1 urbanraw=1; f urbtert urbtert=1
$R code/R/10_attributable_v2.R; $R code/R/11_skill.R
$R code/R/12_onestep.R out/v2_primary.rds; $R code/R/12_onestep.R out/v2_ctrymonth.rds
$R code/R/15_urban_effect.R out/v2_urban.rds; $R code/R/15_urban_effect.R out/v2_urbanraw.rds; $R code/R/16_tertile_effect.R
$R code/R/13_export_v2.R
for p in fig4_v2 fig5_v2 fig6_calendar fig7_urban maps; do python3 code/python/$p.py; done
