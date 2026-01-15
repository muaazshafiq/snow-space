# -*- coding: utf-8 -*-
"""
Brampton Winter Snow Signals (Sentinel-2 NDSI + Sentinel-1 SIND)
- Weekly time-series with robust debugging/logging.
- Works in Earth Engine Python API.

Dependencies:
  pip install earthengine-api geemap matplotlib

One-time:
  earthengine authenticate

Edit:
  PROJECT_ID, AOI (lat/lon/buffer), DATE RANGE
"""

import sys
import traceback
import datetime as dt
from collections import defaultdict

import ee
import numpy as np
import matplotlib.pyplot as plt

# ---------------- CONFIG ----------------
PROJECT_ID = "ee-bramhacks"        # <- CHANGE to your EE-enabled GCP project
LAT, LON = 43.7000, -79.7600       # Brampton approx center
BUFFER_M = 2000                    # AOI buffer radius in meters
START_DATE = "2023-12-01"
END_DATE   = "2024-04-15"

# S2 params
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
S2_MAX_CLOUD = 60  # relax to capture more winter dates

# S1 params
S1_COLLECTION = "COPERNICUS/S1_GRD"
S1_BASELINE_START = "2023-08-01"   # late-summer, snow-free
S1_BASELINE_END   = "2023-09-15"

# Reduction params
REDUCE_SCALE_S2 = 20   # SWIR1 is 20m; okay to keep 20m for NDSI mean
REDUCE_SCALE_S1 = 10   # 10m for S1 IW GRD
MAX_PIXELS = 1_000_000_000
TILE_SCALE = 2

# Heuristic thresholds (for quick interpretation)
S2_SNOW_THRESH = 0.10     # NDSI ~0.1+
S1_SNOW_BAND   = (0.05, 0.15)  # typical SIND snow-ish band (tune per area)

# ----------------------------------------


def log(msg):
    print(f"[LOG] {msg}", flush=True)


def warn(msg):
    print(f"[WARN] {msg}", flush=True)


def err(msg):
    print(f"[ERR] {msg}", file=sys.stderr, flush=True)


def weekly_mean(dates_str, values):
    """
    Bin dates/values into ISO (year, week) weekly means.
    Returns: (list(datetime), list(float))
    """
    bucket = defaultdict(list)
    for d, v in zip(dates_str, values):
        if v is None:
            continue
        try:
            d0 = dt.datetime.strptime(d, "%Y-%m-%d").date()
            iso = d0.isocalendar()  # (year, week, weekday)
            bucket[(iso[0], iso[1])].append(float(v))
        except Exception as e:
            warn(f"Bad date/value pair: {d} / {v} ({e})")

    out_dates, out_vals = [], []
    for (y, w) in sorted(bucket.keys()):
        # mid-week (Thu = 4) for plotting
        out_dates.append(dt.datetime.fromisocalendar(y, w, 4))
        out_vals.append(float(np.nanmean(bucket[(y, w)])))
    return out_dates, out_vals


def init_ee(project_id):
    try:
        ee.Initialize(project=project_id)
        log(f"Initialized Earth Engine with project: {project_id}")
    except Exception as e:
        err("Failed to initialize EE. Did you run `earthengine authenticate` and set a valid project?")
        raise


def get_aoi(lat, lon, buffer_m):
    geom = ee.Geometry.Point([lon, lat]).buffer(buffer_m)
    return geom


def build_s2_timeseries(aoi, start_date, end_date):
    log("Building Sentinel-2 time series (NDSI)...")
    s2 = (ee.ImageCollection(S2_COLLECTION)
          .filterBounds(aoi)
          .filterDate(start_date, end_date)
          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', S2_MAX_CLOUD)))

    def mask_s2_clouds(img):
        # Mask out cloud, cirrus, cloud shadow using SCL
        scl = img.select('SCL')
        good = scl.remap([3, 8, 9, 10], [0, 0, 0, 0], 1)  # 0=bad, 1=good
        return img.updateMask(good)

    def add_ndsi(img):
        # NDSI = (Green - SWIR1) / (Green + SWIR1) = (B3 - B11)/(B3 + B11)
        ndsi = img.normalizedDifference(['B3', 'B11']).rename('NDSI')
        return img.addBands(ndsi).copyProperties(img, ['system:time_start'])

    s2 = s2.map(mask_s2_clouds).map(add_ndsi)

    # Per-image mean over AOI
    def s2_feat(img):
        stats = img.select('NDSI').reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=REDUCE_SCALE_S2,
            maxPixels=MAX_PIXELS,
            tileScale=TILE_SCALE
        )
        return ee.Feature(None, {
            'date': img.date().format('YYYY-MM-dd'),
            'NDSI': stats.get('NDSI')
        })

    feats = s2.map(s2_feat).filter(ee.Filter.notNull(['NDSI']))

    # Pull to client
    dates = feats.aggregate_array('date').getInfo()
    vals  = feats.aggregate_array('NDSI').getInfo()

    log(f"S2 observations (post-cloudmask): {len(dates)}")
    if len(dates) == 0:
        warn("No S2 points. Consider relaxing cloud filter or enlarging AOI.")
    else:
        # Quick debug: first/last and sample values
        log(f"S2 first date: {dates[0]}, last date: {dates[-1]}")
        log(f"S2 sample values (first 5): {vals[:5]}")

    return dates, vals


def build_s1_timeseries(aoi, start_date, end_date):
    log("Building Sentinel-1 time series (SIND from VV)...")

    # Merge ASC + DESC passes to maximize coverage
    s1_main = (ee.ImageCollection(S1_COLLECTION)
               .filterBounds(aoi)
               .filterDate(start_date, end_date)
               .filter(ee.Filter.eq('instrumentMode', 'IW'))
               .select(['VV']))

    size_check = s1_main.size().getInfo()
    log(f"S1 IW VV images in window (pre-merge): {size_check}")
    if size_check == 0:
        warn("No S1 images found in time window. Check AOI or dates.")

    # Baseline (late summer, ASC + DESC, median)
    s1_ref = (ee.ImageCollection(S1_COLLECTION)
              .filterBounds(aoi)
              .filterDate(S1_BASELINE_START, S1_BASELINE_END)
              .filter(ee.Filter.eq('instrumentMode', 'IW'))
              .select('VV')
              .median()
              .clip(aoi))

    # Derive SIND = (ref - cur) / (ref + cur), both in linear units
    def add_sind(img):
        sind = s1_ref.subtract(img.select('VV')).divide(s1_ref.add(img.select('VV'))).rename('SIND_VV')
        return sind.copyProperties(img, ['system:time_start'])

    s1_sind = s1_main.map(add_sind)

    def s1_feat(img):
        stats = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=REDUCE_SCALE_S1,
            maxPixels=MAX_PIXELS,
            tileScale=TILE_SCALE
        )
        return ee.Feature(None, {
            'date': img.date().format('YYYY-MM-dd'),
            'SIND': stats.get('SIND_VV')
        })

    feats = s1_sind.map(s1_feat).filter(ee.Filter.notNull(['SIND']))

    dates = feats.aggregate_array('date').getInfo()
    vals  = feats.aggregate_array('SIND').getInfo()

    log(f"S1 observations: {len(dates)}")
    if len(dates) == 0:
        warn("No S1 SIND points returned. Check filters and baseline window.")
    else:
        log(f"S1 first date: {dates[0]}, last date: {dates[-1]}")
        log(f"S1 sample values (first 5): {vals[:5]}")

    return dates, vals


def main():
    try:
        init_ee(PROJECT_ID)
        aoi = get_aoi(LAT, LON, BUFFER_M)
        log(f"AOI set: lat={LAT}, lon={LON}, buffer={BUFFER_M} m")
        log(f"Window: {START_DATE} → {END_DATE}")

        # Build time series
        s2_dates, s2_vals = build_s2_timeseries(aoi, START_DATE, END_DATE)
        s1_dates, s1_vals = build_s1_timeseries(aoi, START_DATE, END_DATE)

        # Weekly binning
        s2_wd, s2_wv = weekly_mean(s2_dates, s2_vals)
        s1_wd, s1_wv = weekly_mean(s1_dates, s1_vals)
        log(f"S2 weekly points: {len(s2_wd)} | S1 weekly points: {len(s1_wd)}")

        # Debug if empty series
        if len(s2_wd) == 0:
            warn("S2 weekly series empty (clouds?). Try higher S2_MAX_CLOUD or larger AOI.")
        if len(s1_wd) == 0:
            warn("S1 weekly series empty. Sanity-check S1 collection presence with a raw size():\n"
                 "ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(aoi)"
                 ".filterDate(start, end).filter(ee.Filter.eq('instrumentMode','IW')).size().getInfo()")

        # Plot
        xmin = dt.datetime.strptime(START_DATE, "%Y-%m-%d")
        xmax = dt.datetime.strptime(END_DATE, "%Y-%m-%d")

        plt.figure(figsize=(12,4))
        if len(s2_wd):
            plt.plot(s2_wd, s2_wv, 'o-', label='S2 NDSI (weekly mean)')
        if len(s1_wd):
            plt.plot(s1_wd, s1_wv, 'o-', label='S1 SIND (weekly mean)')

        plt.axhline(S2_SNOW_THRESH, linestyle='--', label=f'Snow threshold ~{S2_SNOW_THRESH}')
        plt.xlim(xmin, xmax)
        plt.title('Brampton Winter 2023–2024 — Snow Signals (S2 NDSI & S1 SIND)')
        plt.ylabel('Index value')
        plt.xlabel('Date')
        plt.grid(True, linestyle=':')
        plt.legend()
        plt.tight_layout()
        plt.show()

        # Quick textual summary
        if len(s2_wd):
            s2_above = sum(1 for v in s2_wv if v is not None and v >= S2_SNOW_THRESH)
            log(f"S2 weeks ≥ {S2_SNOW_THRESH}: {s2_above}/{len(s2_wd)} (clear-sky only)")
        if len(s1_wd):
            band_lo, band_hi = S1_SNOW_BAND
            s1_snowish = sum(1 for v in s1_wv if v is not None and band_lo <= v <= band_hi)
            log(f"S1 weeks in SIND band {S1_SNOW_BAND}: {s1_snowish}/{len(s1_wd)} (all-weather)")

        # Print sample table (first 8 rows) for quick debug
        rows = []
        for d, v in zip(s2_wd[:8], s2_wv[:8]):
            rows.append(("S2", d.strftime("%Y-%m-%d"), round(v, 4) if v is not None else None))
        for d, v in zip(s1_wd[:8], s1_wv[:8]):
            rows.append(("S1", d.strftime("%Y-%m-%d"), round(v, 4) if v is not None else None))
        if rows:
            log("Sample (first up to 8 per series):")
            for r in rows:
                print(f"  {r[0]}  {r[1]}  {r[2]}")

    except Exception as e:
        err("Unhandled exception:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
