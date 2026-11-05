/**** Paper 3 – province population (WorldPop) and urban built-up fraction (GHSL), 232 provinces, 8 countries
 * Paste into the Google Earth Engine Code Editor (code.earthengine.google.com) and press Run.
 * Step 0: upload P3_provinces_ADM1_shapefile.zip as a Table asset (Assets > New > Shape files),
 *         name it P3_provinces_ADM1, then set ASSET below to its path.
 * Output: two CSVs in your Google Drive folder EE_Paper3 (Tasks tab > Run each export).
 * Before running, check these dataset IDs on the Earth Engine catalogue, in case they have been renamed:
 *   WorldPop/GP/100m/pop                 (band 'population', yearly 2000–2020, 100 m)
 *   JRC/GHSL/P2023A/GHS_BUILT_S          (band 'built_surface', m² per 100 m cell, 5-year epochs)
 ****/
var ASSET = 'projects/YOUR-PROJECT/assets/P3_provinces_ADM1';   // <-- edit
var prov = ee.FeatureCollection(ASSET);
print('Provinces (expect 232):', prov.size());

// ---------- 1. Population, WorldPop constrained-free 100 m, 2010–2020 ----------
var wp = ee.ImageCollection('WorldPop/GP/100m/pop');
var years = ee.List.sequence(2010, 2020);
var popRows = ee.FeatureCollection(years.map(function (y) {
  y = ee.Number(y);
  var img = wp.filter(ee.Filter.eq('year', y)).select('population').mosaic();
  var stats = img.reduceRegions({collection: prov, reducer: ee.Reducer.sum(), scale: 100, tileScale: 8});
  return stats.map(function (f) {
    return ee.Feature(null, {iso3: f.get('iso3'), shapeID: f.get('shapeID'), shapeName: f.get('shapeName'),
                             year: y, population: f.get('sum')});
  });
})).flatten();

Export.table.toDrive({collection: popRows, description: 'P3_worldpop_province_year_2010_2020',
  folder: 'EE_Paper3', fileFormat: 'CSV', selectors: ['iso3', 'shapeID', 'shapeName', 'year', 'population']});

// ---------- 2. Built-up fraction, GHSL P2023A, epochs 2010, 2015, 2020 ----------
var built = ee.ImageCollection('JRC/GHSL/P2023A/GHS_BUILT_S');
var epochs = ee.List([2010, 2015, 2020]);
var area = ee.Image.pixelArea().rename('area_m2');
var builtRows = ee.FeatureCollection(epochs.map(function (y) {
  y = ee.Number(y);
  var b = built.filter(ee.Filter.calendarRange(y, y, 'year')).first().select('built_surface').rename('built_m2');
  var img = b.addBands(area.reproject(b.projection()));
  var stats = img.reduceRegions({collection: prov, reducer: ee.Reducer.sum(), scale: 100, tileScale: 8});
  return stats.map(function (f) {
    var bm = ee.Number(f.get('built_m2')); var am = ee.Number(f.get('area_m2'));
    return ee.Feature(null, {iso3: f.get('iso3'), shapeID: f.get('shapeID'), shapeName: f.get('shapeName'), epoch: y,
                             built_m2: bm, area_m2: am, built_fraction: bm.divide(am)});
  });
})).flatten();

Export.table.toDrive({collection: builtRows, description: 'P3_ghsl_builtup_province_epoch',
  folder: 'EE_Paper3', fileFormat: 'CSV',
  selectors: ['iso3', 'shapeID', 'shapeName', 'epoch', 'built_m2', 'area_m2', 'built_fraction']});

// Quick visual check
Map.addLayer(prov, {color: '2a78d6'}, 'Provinces');
Map.addLayer(built.filter(ee.Filter.calendarRange(2020, 2020, 'year')).first().select('built_surface'),
             {min: 0, max: 5000, palette: ['fcfcfb', 'eb6834', '8f1d1c']}, 'Built-up 2020', false);
