# SnowSpace-BramHacks Winner

A snow removal job marketplace app that helps users find and complete snow shoveling jobs in Brampton, Ontario. Jobs are prioritized based on traffic levels and snow coverage (NDSI) to optimize snow removal efforts in high-priority areas.

## What is SnowSpace?

SnowSpace combines real-time snow coverage data with traffic patterns to create a dynamic job marketplace for snow removal. Streets are scored and prioritized based on:
- **Traffic Score**: How busy the street is (higher traffic = higher priority)
- **NDSI Score** (Normalized Difference Snow Index): Amount of snow coverage detected via satellite imagery
- **Dynamic Pricing**: Job payouts increase over time based on priority and how long the job has been available

## Team Contributions

This project was built collaboratively:
- **Training Data & Traffic Scores**: Data processing pipeline for traffic and NDSI scoring
- **Frontend & Logic**: Interactive Svelte app with job listings, maps, and filtering
- **Snow Score Calculation**: Google Earth Engine integration for satellite-based NDSI calculation

## Quick Start

### Running the Web App

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   - Navigate to `http://localhost:5173` (or the URL shown in terminal)
   - You'll see the SnowSpace landing page with authentication options
   - Click "Skip" to go directly to the job map

### Running Data Processing Scripts

The data processing pipeline requires Python and Node.js:

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   # Or use the setup script:
   ./setup.sh
   ```

2. **See detailed documentation in `docs/` for:**
   - Traffic scoring system ([docs/TRAFFIC_SCORING.md](docs/TRAFFIC_SCORING.md))
   - Quick reference guide ([docs/QUICKSTART.md](docs/QUICKSTART.md))
   - Manual data download instructions ([docs/MANUAL_DOWNLOAD.md](docs/MANUAL_DOWNLOAD.md))

## Project Structure

```
snowspace/
├── README.md                    # This file
├── package.json                 # Frontend dependencies
├── requirements.txt             # Python dependencies
├── setup.sh                     # Python setup script
│
├── src/                         # Svelte frontend application
│   ├── routes/                  # SvelteKit routes
│   │   ├── +page.svelte        # Landing page (auth)
│   │   ├── +layout.svelte      # Root layout
│   │   └── home/               # Main app page
│   │       └── +page.svelte    # Job map and listings
│   ├── lib/                    # Reusable components
│   │   ├── components/
│   │   │   ├── Drawer.svelte   # Bottom drawer UI
│   │   │   └── StreetCard.svelte # Job card component
│   │   └── styles/
│   │       └── global.css      # Global styles
│   └── app.html                # HTML template
│
├── static/                     # Static assets
│   ├── icons/                  # SVG icons
│   ├── fonts/                  # Custom fonts
│   └── data/
│       └── ndsi_data.csv       # Frontend data (served to browser)
│
├── scripts/                    # Utility scripts
│   ├── data_processing/        # Data generation scripts
│   │   ├── snow.py            # NDSI calculation (Google Earth Engine)
│   │   ├── add_scores.py      # Score calculation
│   │   ├── add_traffic_scores.py # Traffic score addition
│   │   └── add-addresses.js   # Geocoding (reverse geocode coordinates)
│   ├── traffic_scoring/        # Traffic scoring system
│   │   ├── traffic_scorer.py  # Full traffic scorer (with OSM)
│   │   ├── traffic_scorer_simple.py # Simple traffic scorer
│   │   ├── download_helper.py # Data download utilities
│   │   └── example_usage.py   # Usage examples
│   └── test.py                # Test script
│
├── data/                       # Data files
│   ├── brampton_traffic_data/ # Brampton traffic volume data
│   └── roads_circle_vertices_with_traffic.csv # Road vertices with scores
│
├── docs/                       # Documentation
│   ├── TRAFFIC_SCORING.md     # Traffic scoring overview
│   ├── TRAFFIC_SCORING_FULL.md # Complete traffic scoring docs
│   ├── QUICKSTART.md          # Quick reference
│   └── MANUAL_DOWNLOAD.md     # Manual data download guide
│
├── ndsi_data.csv              # Source data (used by scripts)
├── svelte.config.js           # SvelteKit configuration
├── vite.config.js             # Vite configuration
└── jsconfig.json              # JavaScript configuration
```

## How It Works

### 1. Data Collection & Processing

The data pipeline combines multiple sources:

**Traffic Data:**
- Official traffic volume data from City of Brampton GeoHub
- OpenStreetMap road network for Brampton
- K-nearest neighbors spatial interpolation for traffic scores
- See `scripts/traffic_scoring/` for implementation

**Snow Coverage Data:**
- NDSI (Normalized Difference Snow Index) from Sentinel-2 satellite imagery
- Calculated using Google Earth Engine API
- See `scripts/data_processing/snow.py` for implementation

**Combined Scoring:**
- Priority score = `traffic_score * ndsi`
- Normalized to 0-10 scale using z-score normalization
- Higher scores indicate more critical snow removal needs

### 2. Frontend Application

The Svelte app provides an interactive interface:

**Features:**
- **Interactive Map**: Visualizes all streets with color-coded priority
- **Radius Filter**: Adjustable search radius (10-250 km)
- **Job Listings**: Scrollable cards with street details and payouts
- **Dynamic Pricing**: Job payouts increase every minute based on priority
- **Sorting Options**: Filter by payout, priority, or alphabetically
- **Statistics Dashboard**: Track earnings, job count, and averages

**Data Flow:**
1. Frontend loads `ndsi_data.csv` from `/data/` endpoint
2. CSV contains: coordinates, traffic scores, NDSI values, street addresses
3. Priority scores calculated client-side
4. Jobs filtered by radius and sorted by user preference
5. Prices recalculate every 60 seconds with countdown timer

### 3. Priority Calculation

```
Raw Score = traffic_score × ndsi
Z-Score = (raw_score - mean) / standard_deviation
Priority = clamp(5.5 + (z_score × 1.5), 1, 10)
```

Priority levels:
- **1-3**: Low priority (residential streets with minimal traffic/snow)
- **4-6**: Medium priority (secondary roads)
- **7-9**: High priority (arterial roads, significant snow)
- **10**: Critical priority (busy highways/intersections with heavy snow)

### 4. Dynamic Pricing Model

Base payout: $100

Growth rate varies by priority:
- Priority 0: 0.1% per minute
- Priority 10: 1.0% per minute

```
current_payout = base_payout × (1 + growth_rate)^minutes_elapsed
```

Example:
- Priority 8 job, 60 minutes old: ~$130
- Priority 3 job, 60 minutes old: ~$103

## Data Sources

- **City of Brampton Traffic Volumes**: [geohub.brampton.ca](https://geohub.brampton.ca)
- **OpenStreetMap**: Road network data
- **Sentinel-2 Satellite Imagery**: Via Google Earth Engine (NDSI calculation)
- **Nominatim Geocoding**: Street address lookup

## Development

### Frontend

```bash
npm run dev       # Start dev server
npm run build     # Build for production
npm run preview   # Preview production build
```

### Data Processing

**Generate NDSI scores:**
```bash
cd scripts/data_processing
python snow.py  # Requires Google Earth Engine credentials
```

**Add street addresses:**
```bash
cd scripts/data_processing
node add-addresses.js  # Uses Nominatim API (rate-limited)
```

**Traffic scoring:**
```bash
cd scripts/traffic_scoring
python traffic_scorer_simple.py  # Run simple scorer
python example_usage.py          # See usage examples
```

## Configuration

### Environment Variables

For Google Earth Engine (NDSI calculation):
- Set up GEE authentication: `earthengine authenticate`
- Configure project ID in `scripts/data_processing/snow.py`

### Data Paths

If you need to update data file locations:
- Frontend data: `static/data/ndsi_data.csv` (served at `/data/ndsi_data.csv`)
- Processing scripts: `ndsi_data.csv` (root level)
- Traffic data cache: `data/brampton_traffic_data/`

## Performance

**Frontend:**
- Loads 30,000+ coordinate points efficiently
- Client-side filtering and sorting
- SVG-based map with hover tooltips
- Real-time price updates every 60 seconds

**Traffic Scoring:**
- Single lookup: ~0.5-1 ms per coordinate
- Batch processing: ~28,700 coordinates/second
- KD-tree spatial index for O(log n) lookups

## Documentation

- [Traffic Scoring Overview](docs/TRAFFIC_SCORING.md) - Quick start for traffic scoring
- [Complete Traffic Scoring Docs](docs/TRAFFIC_SCORING_FULL.md) - Full API reference
- [Quick Reference](docs/QUICKSTART.md) - Quick commands and examples
- [Manual Download Guide](docs/MANUAL_DOWNLOAD.md) - If automatic downloads fail

## License

MIT

## Credits

**Data Sources:**
- City of Brampton GeoHub
- OpenStreetMap Contributors
- European Space Agency (Sentinel-2 imagery)
- Nominatim/OpenStreetMap (geocoding)

**Technologies:**
- SvelteKit 2
- Vite
- Python (pandas, geopandas, scipy)
- Google Earth Engine
- OSMnx (OpenStreetMap data)
