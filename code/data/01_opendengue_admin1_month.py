"""OpenDengue v1.3 subnational extract -> province-month case counts.
Input: data/raw/Spatial_extract_V1_3.csv (download from https://opendengue.org, version 1.3; not redistributed here).
Keeps first- and second-level records with weekly or monthly resolution, assigns each record to the month in which it starts,
and sums within first-level unit and month. Output: data/intermediate/P3_dengue_admin1_month_OpenDengue.csv"""
import pandas as pd
sp = pd.read_csv('data/raw/Spatial_extract_V1_3.csv', usecols=['adm_0_name', 'adm_1_name', 'adm_2_name', 'ISO_A0', 'FAO_GAUL_code',
     'calendar_start_date', 'calendar_end_date', 'dengue_total', 'case_definition_standardised', 'S_res', 'T_res'], low_memory=False)
sp = sp[sp.S_res.isin(['Admin1', 'Admin2']) & sp.T_res.isin(['Week', 'Month'])]
sp['calendar_start_date'] = pd.to_datetime(sp.calendar_start_date)
sp['year'] = sp.calendar_start_date.dt.year; sp['month'] = sp.calendar_start_date.dt.month
sp1 = sp.groupby(['ISO_A0', 'adm_0_name', 'adm_1_name', 'S_res', 'year', 'month']).agg(dengue_cases=('dengue_total', 'sum'), n_records=('dengue_total', 'size'),
      n_adm2_units=('adm_2_name', 'nunique'), case_definition=('case_definition_standardised', 'first'), temporal_res=('T_res', 'first')).reset_index() \
      .rename(columns={'ISO_A0': 'iso3', 'S_res': 'source_spatial_res'})
sp1.to_csv('data/intermediate/P3_dengue_admin1_month_OpenDengue.csv', index=False); print(sp1.shape)
