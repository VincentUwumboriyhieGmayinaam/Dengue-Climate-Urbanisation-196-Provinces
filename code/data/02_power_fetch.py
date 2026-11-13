"""NASA POWER monthly climate (MERRA-2, 0.5 degree) for the grid cells under up to five sample points per province.
Input: data/raw/power_points.json [iso3, shapeName, shapeID, point index, lat, lon].
Output: data/raw/power_results.json {cell: [[YYYYMM, T2M, T2M_MAX, PRECTOTCORR (mm/day), RH2M], ...]}.
The cached results used in the paper (retrieved 2 November 2026) are included in data/raw/, so this step is only needed to
re-download. API: https://power.larc.nasa.gov/docs/services/api/temporal/monthly/"""
import json, time, urllib.request
P = json.load(open('data/raw/power_points.json'))
cells = sorted({(round(p[4] * 2) / 2, round(p[5] * 2) / 2) for p in P})
URL = ('https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M,T2M_MAX,PRECTOTCORR,RH2M&community=AG'
       '&latitude={lat}&longitude={lon}&start=2009&end=2023&format=JSON')
out = {}
for lat, lon in cells:
    d = json.load(urllib.request.urlopen(URL.format(lat=lat, lon=lon), timeout=120))['properties']['parameter']
    keys = sorted(k for k in d['T2M'] if not k.endswith('13'))           # drop the annual value (month 13)
    out[f'{lat},{lon}'] = [[k, d['T2M'][k], d['T2M_MAX'][k], d['PRECTOTCORR'][k], d['RH2M'][k]] for k in keys]
    time.sleep(1)
json.dump(out, open('data/raw/power_results.json', 'w')); print(len(out), 'cells')
