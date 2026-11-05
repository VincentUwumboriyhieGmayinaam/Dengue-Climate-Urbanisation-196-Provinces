"""Province built-up fraction and population from GHSL R2023A 1 km global rasters (Mollweide, ESRI:54009).
Reads each GeoTIFF directly from its zip (no extraction). Writes P3_ghsl_province_epoch.csv:
iso3, shapeID, epoch, built_m2, land_km2 (cells with data), pop, built_fraction."""
import sys, zipfile, glob, numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.mask import mask
ZDIR = sys.argv[1]
G = gpd.read_file('zip://data/boundaries/P3_provinces_ADM1_shapefile.zip!P3_provinces_ADM1.shp').to_crs('ESRI:54009')
rows = []
for kind in ('BUILT_S', 'POP'):
    for zp in sorted(glob.glob(f'{ZDIR}/GHS_{kind}_E*_GLOBE_R2023A_54009_1000_V1_0.zip')):
        ep = int(zp.split('_E')[1][:4]); tif = [n for n in zipfile.ZipFile(zp).namelist() if n.endswith('.tif')][0]
        with rasterio.open(f'/vsizip/{zp}/{tif}') as src:
            nod = src.nodata
            for _, g in G.iterrows():
                arr, _ = mask(src, [g.geometry], crop=True, filled=True, nodata=nod if nod is not None else -200)
                a = arr[0].astype('float64'); ok = a != (nod if nod is not None else -200); ok &= a >= 0
                rows.append(dict(iso3=g.iso3, shapeID=g.shapeID, epoch=ep, kind=kind, value=a[ok].sum(), cells=int(ok.sum())))
        print('done', kind, ep, flush=True)
R = pd.DataFrame(rows)
W = R.pivot_table(index=['iso3', 'shapeID', 'epoch'], columns='kind', values='value').reset_index()
C = R[R.kind == 'BUILT_S'].set_index(['shapeID', 'epoch']).cells
W['land_km2'] = W.set_index(['shapeID', 'epoch']).index.map(C).values
W['built_fraction'] = W.BUILT_S / (W.land_km2 * 1e6)
W = W.rename(columns={'BUILT_S': 'built_m2', 'POP': 'pop'})
W.to_csv('data/P3_ghsl_province_epoch.csv', index=False)
print(W.groupby(['iso3', 'epoch']).agg(pop_m=('pop', lambda s: s.sum() / 1e6), built_med=('built_fraction', 'median')).round(3).to_string())
