# Quick Start Guide

Get up and running in 3 steps:

## 1. Install Dependencies

```bash
# Option A: Use the setup script (recommended)
./setup.sh

# Option B: Manual installation
pip install -r requirements.txt
```

## 2. Run the Example

```bash
python traffic_scorer.py
```

First run will:
- Download Brampton traffic data from GeoHub (~2-5 minutes)
- Download OpenStreetMap road network
- Build spatial index
- Cache everything locally

**Subsequent runs are instant!**

## 3. Use in Your Code

```python
from traffic_scorer import BramptonTrafficScorer

# Initialize once
scorer = BramptonTrafficScorer()
scorer.prepare_data()

# Score any coordinate in Brampton
score = scorer.get_traffic_score(lon=-79.7617, lat=43.6532)
print(f"Traffic score: {score:.3f}")  # 0.0 to 1.0

# Batch score 30,000 coordinates
coords = [(-79.70, 43.70), (-79.75, 43.65), ...]
scores = scorer.batch_score(coords)
```

That's it! See `README.md` for full documentation.

## Performance

- **Single lookup**: ~0.5-1 ms
- **30,000 coordinates**: ~15-30 seconds
- **Data downloads**: Only once, then cached

## Example Output

```
Location (-79.7617, 43.6532): Traffic Score = 0.756
Location (-79.7500, 43.6500): Traffic Score = 0.623
Location (-79.6500, 43.7500): Traffic Score = 0.412
```

Score interpretation:
- **0.0-0.3**: Low traffic (residential areas)
- **0.3-0.6**: Moderate traffic (secondary roads)
- **0.6-0.8**: High traffic (arterial roads)
- **0.8-1.0**: Very high traffic (major highways, busy intersections)

## Need Help?

See `example_usage.py` for more examples or read the full `README.md`.
