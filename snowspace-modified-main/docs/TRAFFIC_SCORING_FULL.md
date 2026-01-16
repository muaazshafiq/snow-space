# Brampton Traffic Scorer

A fast, efficient system for scoring traffic levels at any coordinate in Brampton, Ontario. Scores range from 0 (lowest traffic) to 1 (highest traffic).

## Features

- **Fast Lookups**: O(log n) time complexity using spatial indexing (KD-tree)
- **One-Time Download**: Downloads data once, then caches locally
- **Hybrid Approach**: Combines actual traffic count data + OpenStreetMap road network
- **Batch Processing**: Efficiently score 30,000+ coordinates
- **Smart Interpolation**: Uses k-nearest neighbors with inverse distance weighting

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the example to download data and test:
```bash
python traffic_scorer.py
```

This will:
- Download Brampton traffic volume data from GeoHub
- Download OpenStreetMap road network for Brampton
- Build spatial index for fast lookups
- Cache everything locally for future use
- Run performance tests

## Quick Start

```python
from traffic_scorer import BramptonTrafficScorer

# Initialize (only once at app startup)
scorer = BramptonTrafficScorer()
scorer.prepare_data()  # Downloads data first time, uses cache after

# Score a single coordinate
score = scorer.get_traffic_score(lon=-79.7617, lat=43.6532)
print(f"Traffic score: {score:.3f}")  # 0.0 to 1.0

# Score 30,000 coordinates efficiently
coordinates = [(lon1, lat1), (lon2, lat2), ...]  # Your coordinates
scores = scorer.batch_score(coordinates)
```

## How It Works

### Data Sources

1. **Brampton Traffic Volumes** (from geohub.brampton.ca)
   - Official traffic count data from the City of Brampton
   - Contains actual measured traffic volumes at key locations

2. **OpenStreetMap Road Network**
   - Complete road network for Brampton
   - Road classifications (highway, arterial, residential, etc.)
   - Used to estimate traffic between measured points

### Scoring Algorithm

1. **Data Fusion**:
   - Real traffic counts at measurement locations
   - Estimated traffic based on road types (highways > arterials > residential)
   - Combines ~300 real counts with ~10,000 road segments

2. **Normalization**:
   - Scores normalized to 0-1 range
   - Uses 95th percentile to avoid outlier skew

3. **Spatial Interpolation** (k-Nearest Neighbors):
   - For any query coordinate, finds k nearest points (default k=5)
   - Uses inverse distance weighting for interpolation
   - Closer points have more influence on the score

4. **Fast Lookups**:
   - KD-tree spatial index for O(log n) query time
   - Typically < 1ms per coordinate lookup

## Performance

Based on testing with 1,000 random coordinates:

- **Lookup time**: ~0.5-1.0 ms per coordinate
- **Throughput**: ~1,000-2,000 coordinates/second
- **30,000 coordinates**: ~15-30 seconds total
- **Memory usage**: ~50-100 MB (cached data)

## Usage Examples

### Example 1: Score a Single Location

```python
from traffic_scorer import BramptonTrafficScorer

scorer = BramptonTrafficScorer()
scorer.prepare_data()

# Brampton City Hall area
score = scorer.get_traffic_score(-79.7617, 43.6532)
print(f"Traffic score: {score:.3f}")
```

### Example 2: Process CSV File

```python
import pandas as pd
from traffic_scorer import BramptonTrafficScorer

# Load your coordinates
df = pd.read_csv('locations.csv')  # columns: lon, lat

# Initialize scorer
scorer = BramptonTrafficScorer()
scorer.prepare_data()

# Score all coordinates
coords = list(zip(df['lon'], df['lat']))
df['traffic_score'] = scorer.batch_score(coords)

# Save results
df.to_csv('locations_with_scores.csv', index=False)
```

### Example 3: Real-time API

```python
from flask import Flask, jsonify, request
from traffic_scorer import BramptonTrafficScorer

app = Flask(__name__)

# Initialize once at startup
scorer = BramptonTrafficScorer()
scorer.prepare_data()

@app.route('/traffic_score')
def get_score():
    lon = float(request.args.get('lon'))
    lat = float(request.args.get('lat'))

    score = scorer.get_traffic_score(lon, lat)

    return jsonify({
        'lon': lon,
        'lat': lat,
        'traffic_score': score
    })

if __name__ == '__main__':
    app.run()
```

### Example 4: Custom Parameters

```python
# Use more neighbors for smoother interpolation
score = scorer.get_traffic_score(lon, lat, k=10)

# Use fewer neighbors for more local estimates
score = scorer.get_traffic_score(lon, lat, k=3)

# Adjust maximum search distance (in degrees)
score = scorer.get_traffic_score(lon, lat, max_distance=0.005)
```

## Advanced Configuration

### Custom Data Directory

```python
scorer = BramptonTrafficScorer(data_dir="/path/to/data")
```

### Cache Behavior

The system caches:
- Downloaded traffic data (`brampton_traffic.geojson`)
- Road network data (`brampton_roads.pkl`)
- Processed spatial index (`scorer_cache.pkl`)

To force re-download:
```python
import shutil
shutil.rmtree('./brampton_traffic_data')
scorer.prepare_data()  # Will re-download everything
```

## Data Structure

The scorer creates a spatial index with:
- **Traffic count points**: Real measurements from Brampton GeoHub
- **Road network points**: Road segment centroids with estimated traffic
- **Total indexed points**: ~10,000-15,000 points

Each point has:
- Coordinates (lon, lat)
- Normalized traffic score (0-1)

## Coordinate System

- **Input**: WGS84 (standard GPS coordinates)
  - Longitude: -79.8 to -79.6 (approximately)
  - Latitude: 43.6 to 43.8 (approximately)

## Troubleshooting

### Data Download Fails

If the primary download method fails, the system tries alternative methods. If all fail:

1. Check internet connection
2. Verify Brampton GeoHub is accessible: https://geohub.brampton.ca
3. Try manual download and save to `./brampton_traffic_data/brampton_traffic.geojson`

### Slow First Run

The first run downloads data and builds the index. This can take 2-5 minutes. Subsequent runs use cached data and start instantly.

### Out of Bounds Coordinates

For coordinates outside Brampton, the scorer returns 0.0 (no traffic data available).

## API Reference

### `BramptonTrafficScorer`

**`__init__(data_dir='./data')`**
- Initialize scorer with custom data directory

**`prepare_data()`**
- Download and prepare all data (downloads once, then uses cache)

**`get_traffic_score(lon, lat, k=5, max_distance=0.01)`**
- Get traffic score for a coordinate
- Parameters:
  - `lon`: Longitude (float)
  - `lat`: Latitude (float)
  - `k`: Number of nearest neighbors (int, default=5)
  - `max_distance`: Max search distance in degrees (float, default=0.01)
- Returns: Traffic score (float, 0-1)

**`batch_score(coordinates)`**
- Score multiple coordinates efficiently
- Parameters:
  - `coordinates`: List of (lon, lat) tuples
- Returns: NumPy array of scores

## License

MIT

## Credits

Data sources:
- City of Brampton GeoHub (geohub.brampton.ca)
- OpenStreetMap Contributors
