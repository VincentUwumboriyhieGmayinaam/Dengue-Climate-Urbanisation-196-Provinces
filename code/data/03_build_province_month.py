"""Province-month analysis file: averages NASA POWER climate over each province's sample points (nearest available cell when a
point's cell is missing), derives anomalies from the 2010-20 calendar-month means, matches OpenDengue first-level names to
geoBoundaries provinces (normalised names plus a documented manual crosswalk), sums cases where several OpenDengue names map
to one province, and merges the Oceanic Nino Index. Output: data/P3_dengue_admin1_month_climate.csv, data/admin1_name_crosswalk.csv"""
import json, re, unicodedata, pandas as pd, numpy as np
P = json.load(open('data/raw/power_points.json'))
R = json.load(open('data/raw/power_results.json'))
pts = pd.DataFrame(P, columns=['iso3', 'shapeName', 'shapeID', 'i', 'lat', 'lon'])
pts['cell'] = [f'{round(a*2)/2},{round(b*2)/2}' for a, b in zip(pts.lat, pts.lon)]
rows = []
for cell, recs in R.items():
    for ym, t, tx, pr, rh in recs: rows.append((cell, int(ym[:4]), int(ym[4:6]), t, tx, pr, rh))
C = pd.DataFrame(rows, columns=['cell', 'year', 'month', 'tmean', 'tmax', 'pr_mmday', 'rh']).replace(-999, np.nan)
key = lambda c: ','.join(str(float(x)) for x in c.split(','))
C['cell'] = C.cell.map(key); pts['cell'] = pts.cell.map(key)
have = C.cell.unique()
hv = np.array([[float(x) for x in c.split(',')] for c in have])
def nearest(c):
    if c in set(have): return c, 0.0
    la, lo = (float(x) for x in c.split(',')); d = np.hypot(hv[:, 0] - la, hv[:, 1] - lo); i = d.argmin(); return have[i], float(d[i])
nn = {c: nearest(c) for c in pts.cell.unique()}
pts['cell_used'] = pts.cell.map(lambda c: nn[c][0]); pts['cell_distance_deg'] = pts.cell.map(lambda c: nn[c][1])
M = pts.merge(C.rename(columns={'cell': 'cell_used'}), on='cell_used')
days = pd.to_datetime(dict(year=M.year, month=M.month, day=1)).dt.days_in_month
M['pr_mm'] = M.pr_mmday * days
A = M.groupby(['iso3', 'shapeName', 'shapeID', 'year', 'month']).agg(power_tmean_c=('tmean', 'mean'), power_tmax_c=('tmax', 'mean'), power_precip_mm=('pr_mm', 'mean'),
     power_rel_humidity_pct=('rh', 'mean'), n_points=('i', 'nunique'), max_cell_distance_deg=('cell_distance_deg', 'max')).reset_index()
A['climate_from_nearest_cell'] = (A.max_cell_distance_deg > 0).astype(int)
base = A[A.year.between(2010, 2020)].groupby(['shapeID', 'month'])[['power_tmean_c', 'power_precip_mm']].mean().add_suffix('_base').reset_index()
A = A.merge(base, on=['shapeID', 'month'])
A['power_tmean_anom_c'] = A.power_tmean_c - A.power_tmean_c_base; A['power_precip_anom_mm'] = A.power_precip_mm - A.power_precip_mm_base
A = A.drop(columns=['power_tmean_c_base', 'power_precip_mm_base']).sort_values(['shapeID', 'year', 'month'])
for k in (1, 2, 3):
    for v in ['power_tmean_c', 'power_precip_mm', 'power_rel_humidity_pct']: A[f'{v}_lag{k}m'] = A.groupby('shapeID')[v].shift(k)
# crosswalk OpenDengue admin-1 names -> geoBoundaries
norm = lambda s: re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower().replace('province', '').replace('(departemento)', ''))
manual = {
 'THA': {'BUNGKAN': 'Bueng Kan Province', 'KAMPAENG PHET': 'Kamphaeng Phet Province', 'PHACHINBURI': 'Prachin Buri Province', 'PHRA NAKHON SI AYUDHYA': 'Phra Nakhon Si Ayutthaya Province',
         'PRACHUAP KHILIKHAN': 'Prachuap Khiri Khan Province', 'SAMUT PRAKARN': 'Samut Prakan Province', 'SAMUT SONGKHAM': 'Samut Songkhram Province', 'TRAD': 'Trat Province'},
 'IDN': {'ACEH': 'Aceh', 'NANGROE ACEH DARUSSALAM': 'Aceh', 'BABEL': 'Bangka-Belitung Islands', 'BANGKA BELITUNG': 'Bangka-Belitung Islands', 'D.I YOGYA': 'Special Region of Yogyakarta',
         'DAERAH ISTIMEWA YOGYAKARTA': 'Special Region of Yogyakarta', 'DKI JAKARTA': 'Jakarta Special Capital Region', 'JAWA BARAT': 'West Java', 'JAWA TENGAH': 'Central Java', 'JAWA TIMUR': 'East Java',
         'KALIMANTAN BARAT': 'West Kalimantan', 'KALIMANTAN SELATA': 'South Kalimantan', 'KALIMANTAN SELATAN': 'South Kalimantan', 'KALIMANTAN TENGAH': 'Central Kalimantan',
         'KALIMANTAN TIMUR': 'East Kalimantan', 'KALIMANTAN UTARA': 'North Kalimantan', 'KEPULAUAN RIAU': 'Riau Islands', 'MALUKU UTARA': 'North Maluku',
         'NUSA TENGGARA BARAT': 'West Nusa Tenggara', 'NUSATENGGARA BARAT': 'West Nusa Tenggara', 'NUSA TENGGARA TIMUR': 'East Nusa Tenggara', 'NUSATENGGARA TIMUR': 'East Nusa Tenggara',
         'PAPUA BARAT': 'West Papua', 'PAPUA BARAT DAYA': 'West Papua', 'PAPUA PEGUNUNGAN': 'Papua', 'PAPUA SELATAN': 'Papua', 'PAPUA TENGAH': 'Papua',
         'SULAWESI BARAT': 'West Sulawesi', 'SULAWESI SELATA': 'South Sulawesi', 'SULAWESI SELATAN': 'South Sulawesi', 'SULAWESI TENGAH': 'Central Sulawesi', 'SULAWESI TENGGARA': 'Southeast Sulawesi',
         'SULAWESI UTARA': 'North Sulawesi', 'SUMATERA BARAT': 'West Sumatra', 'SUMATERA SELATA': 'South Sumatra', 'SUMATERA SELATAN': 'South Sumatra', 'SUMATERA UTARA': 'North Sumatra'},
 'COL': {'BARRANQUILLA': 'Atlántico', 'BLIVAR': 'Bolívar', 'CARTAGENA': 'Bolívar', 'SANTA MARTA': 'Magdalena', 'BOGOTA': 'Bogota Capital District', 'CUNDIMARCA': 'Cundinamarca', 'GUAJIRA': 'La Guajira',
         'NORTE SANTANDER': 'Norte de Santander', 'SAN ANDRES': 'Archipiélago de San Andrés, Providencia y Santa Catalina', 'VALLE': 'Valle del Cauca'},
 'BRA': {'RIO DE JANEIRO': 'Rio de Jeneiro', 'RIO GRANDE DO NORTE': 'Rio Granda do Norte'},
 'PER': {'CALLAO': 'El Callao', 'LIMA': 'Lima'},
 'BOL': {},
 'NIC': {'JINOTEGA': 'Jinotega (Departamento)', 'BILWI': 'North Carribean Coast Autonomous Region', 'MATAGALPA': 'Matagalpa (Departemento)', 'REGION AUTONOMA DEL ATLANTICO SUR': 'South Atlantic Autonomous Region', 'ZELAYA CENTRAL': 'South Atlantic Autonomous Region'},
 'AUS': {'ACT': 'Australian Capital Territory', 'NSW': 'New South Wales', 'NT': 'Northern Territory', 'QLD': 'Queensland', 'SA': 'South Australia', 'TAS': 'Tasmania', 'VIC': 'Victoria', 'WA': 'Western Australia'}}
D = pd.read_csv('data/intermediate/P3_dengue_admin1_month_OpenDengue.csv')
D = D[D.iso3.isin(manual)]
gb = pts[['iso3', 'shapeName', 'shapeID']].drop_duplicates()
xw = []
for c in manual:
    gn = {norm(n): n for n in gb[gb.iso3 == c].shapeName}
    for n in D[D.iso3 == c].adm_1_name.dropna().unique():
        m = manual[c].get(n) or gn.get(norm(n)); xw.append(dict(iso3=c, adm_1_name=n, shapeName=m, match='manual' if n in manual[c] else ('exact-normalised' if m else 'unmatched')))
XW = pd.DataFrame(xw).merge(gb, on=['iso3', 'shapeName'], how='left')
D = D.merge(XW[['iso3', 'adm_1_name', 'shapeName', 'shapeID']], on=['iso3', 'adm_1_name'], how='left')
# aggregate cases where several OpenDengue names map to one boundary (e.g. city reports into departments)
D = D.dropna(subset=['shapeID']).groupby(['iso3', 'shapeName', 'shapeID', 'year', 'month']).agg(dengue_cases=('dengue_cases', 'sum'), n_source_units=('adm_1_name', 'nunique'),
      case_definition=('case_definition', 'first')).reset_index()
OUT = A.merge(D[['shapeID', 'year', 'month', 'dengue_cases', 'n_source_units', 'case_definition']], on=['shapeID', 'year', 'month'], how='left')
oni = pd.read_csv('data/raw/NOAA_ONI_monthly.csv'); OUT = OUT.merge(oni, on=['year', 'month'], how='left')
OUT.to_csv('data/P3_dengue_admin1_month_climate.csv', index=False); XW.to_csv('data/admin1_name_crosswalk.csv', index=False)
print(OUT.shape, 'units', OUT.shapeID.nunique(), 'unit-months with cases', OUT.dengue_cases.notna().sum())
print(XW.match.value_counts().to_dict(), XW[XW.shapeID.isna()].to_string())
print(OUT.groupby('iso3').agg(units=('shapeID', 'nunique'), case_months=('dengue_cases', 'count')).to_string())
print(OUT[['power_tmean_c', 'power_precip_mm', 'power_rel_humidity_pct']].describe().round(1).to_string())
