"""Zero-filled copy of the province-month files for the sensitivity analysis: missing Colombian and Peruvian months (2010-22) in
departments that reported cases in at least one month are set to 0. Departments that never reported (Apurimac, Huancavelica, Tacna,
and Lima Metropolitana, whose cases are reported under Lima) are left as they are and so stay excluded. Usage: python3 19a_make_zerofill_data.py <out_dir>"""
import sys, os, pandas as pd
out = sys.argv[1] if len(sys.argv) > 1 else 'zerofill'; os.makedirs(f'{out}/data', exist_ok=True)
for f in ['P3_dengue_admin1_month_climate.csv', 'P3_dengue_admin1_month_climate_pop_urban.csv']:
    D = pd.read_csv(f'data/{f}')
    an = D[D.year.between(2010, 2022)]
    ever = set(an[an.iso3.isin(['COL', 'PER']) & an.dengue_cases.notna()].shapeID)
    m = D.iso3.isin(['COL', 'PER']) & D.shapeID.isin(ever) & D.year.between(2010, 2022) & D.dengue_cases.isna()
    D.loc[m, 'dengue_cases'] = 0; D.to_csv(f'{out}/data/{f}', index=False); print(f, 'months set to zero:', int(m.sum()))
