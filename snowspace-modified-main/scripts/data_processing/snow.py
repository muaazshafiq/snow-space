# ndsi_points_to_csv_local_fn.py

import ee
import pandas as pd
from datetime import datetime, timedelta

def ndsi_points_to_csv(date_str):
    # ---------- CONFIG ----------
    PROJECT_ID   = 'bram-477702'
    CSV_IN       = 'roads_circle_vertices_with_traffic.csv'  # seg_id,vertex_seq,lon,lat,traffic_score
    CSV_OUT      = 'roads_ndsi_sample.csv'
    WINDOW_DAYS  = 1
    BUFFER_M     = 10
    S2_COLL      = 'COPERNICUS/S2_SR_HARMONIZED'
    MAX_PIXELS   = 1e8

    # ---------- INIT ----------
    ee.Initialize(project=PROJECT_ID)

    # ---------- Helpers ----------
    def parse_window(day_str, pad_days):
        day = datetime.strptime(day_str, '%Y-%m-%d')
        start = (day - timedelta(days=pad_days)).strftime('%Y-%m-%d')
        end   = (day + timedelta(days=pad_days+1)).strftime('%Y-%m-%d')
        return start, end

    def mask_s2_clouds(img):
        qa = img.select('QA60')
        cloud_bit  = 1 << 10
        cirrus_bit = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
        return img.updateMask(mask)

    def add_ndsi(img):
        return img.addBands(img.normalizedDifference(['B3','B11']).rename('NDSI'))

    # ---------- Load CSV and build FeatureCollection ----------
    df = pd.read_csv(CSV_IN)

    # Optional thinning; keep every 10th. Remove/adjust as needed.
    df_sub = df.iloc[::10].reset_index(drop=False).rename(columns={'index':'row_id'})

    features = []
    for _, r in df_sub.iterrows():
        lon = float(r['lon'])
        lat = float(r['lat'])
        geom = ee.Geometry.Point([lon, lat])

        feat = (ee.Feature(geom.buffer(BUFFER_M))
                .set({
                    'row_id'       : int(r['row_id']),
                    'seg_id'       : r.get('seg_id', ''),
                    'vertex_seq'   : r.get('vertex_seq', ''),
                    'traffic_score': float(r.get('traffic_score', 0.0)),
                    'lon'          : lon,
                    'lat'          : lat
                }))
        features.append(feat)

    fc = ee.FeatureCollection(features)

    # ---------- Build image for the window ----------
    start, end = parse_window(date_str, WINDOW_DAYS)
    aoi = fc.geometry().bounds(1)

    ic = (ee.ImageCollection(S2_COLL)
          .filterBounds(aoi)
          .filterDate(start, end)
          .map(mask_s2_clouds)
          .map(add_ndsi))

    img = ic.sort('CLOUDY_PIXEL_PERCENTAGE').first()
    if img.getInfo() is None:
        raise RuntimeError(f'No Sentinel-2 image found {start}..{end} over the AOI.')

    used_date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')

    # ---------- Sample NDSI ----------
    sampled = (img.select('NDSI')
                 .reduceRegions(
                     collection=fc,
                     reducer=ee.Reducer.mean(),
                     scale=10)
                 .map(lambda f: f.set({'used_image_date': used_date})))

    records = sampled.getInfo()['features']
    rows = []
    for f in records:
        p = f['properties']
        rows.append({
            'seg_id'        : p.get('seg_id'),
            'vertex_seq'    : p.get('vertex_seq'),
            'lon'           : p.get('lon'),
            'lat'           : p.get('lat'),
            'traffic_score' : p.get('traffic_score'),
            'ndsi'          : p.get('mean'),
            'used_image_date': p.get('used_image_date')
        })

    out = pd.DataFrame(rows)
    out.to_csv(CSV_OUT, index=False)
    print(f'Wrote {len(out)} rows to {CSV_OUT}')

# Example usage:
ndsi_points_to_csv('2024-12-01')
