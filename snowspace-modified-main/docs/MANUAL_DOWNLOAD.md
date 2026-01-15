# Manual Data Download Guide

If automatic download fails, follow these steps:

## Option 1: Download from Browser (Easiest)

1. **Visit the dataset page:**
   - Go to: https://geohub.brampton.ca/datasets/city-of-brampton-traffic-volumes

2. **Download the data:**
   - Look for a "Download" button (usually top-right or in a sidebar)
   - Click on it and select one of these formats:
     - **GeoJSON** (recommended)
     - **CSV** (also works)
     - Shapefile (works but more complex)

3. **Save to the correct location:**
   - Save the downloaded file to: `brampton_traffic_data/`
   - Rename it to one of:
     - `brampton_traffic.geojson` (for GeoJSON)
     - `brampton_traffic.csv` (for CSV)

4. **Run the script again:**
   ```bash
   python traffic_scorer.py
   ```

## Option 2: Find the API Link

If you can't find a download button:

1. **Visit:** https://geohub.brampton.ca/datasets/city-of-brampton-traffic-volumes

2. **Look for "API" or "I want to use this" tab/button**

3. **Find the GeoJSON URL** - it might look like:
   - `https://...arcgis.com/.../FeatureServer/0/query?...f=geojson`
   - Or: `https://geohub.brampton.ca/datasets/...geojson`

4. **Copy the full URL and download:**
   ```bash
   # On Mac/Linux:
   curl "PASTE_URL_HERE" -o brampton_traffic_data/brampton_traffic.geojson

   # Or use browser:
   # Just paste URL in browser address bar and save the file
   ```

## Option 3: Try Alternative Sources

### Peel Region Data (Brampton is part of Peel Region)
- Visit: https://peelregion.ca/services/traffic-data
- They may have traffic count data you can download

### OpenStreetMap Only (Lower accuracy but works)
If you can't find Brampton traffic data, you can run with OSM only:

```python
from traffic_scorer import BramptonTrafficScorer

scorer = BramptonTrafficScorer()

# Skip traffic data, use road network only
scorer.road_network = scorer.download_road_network()
# ... continue with road network only approach
```

## Troubleshooting

### "Access Denied" or "Forbidden"
- The dataset might require authentication
- Try downloading while logged into a Brampton/Peel account if you have one
- Try downloading from a different network (sometimes IP restrictions apply)

### CSV doesn't have coordinates
Make sure your CSV has these columns (names may vary):
- Latitude (or LAT, Y, POINT_Y)
- Longitude (or LON, LONG, X, POINT_X)

### File structure doesn't match
Check if your file has these common traffic data fields:
- AADT (Annual Average Daily Traffic)
- Volume / Count / Traffic_Volume
- Street names or IDs

If the field names are different, you may need to modify the code to recognize them.

## Need Help?

Once you have the file downloaded, place it in `brampton_traffic_data/` directory and the script will automatically detect and load it!

The code looks for these filenames:
- `brampton_traffic.geojson`
- `brampton_traffic.csv`
- `City_of_Brampton_Traffic_Volumes.geojson`
- `City_of_Brampton_Traffic_Volumes.csv`

Any of these will work!
