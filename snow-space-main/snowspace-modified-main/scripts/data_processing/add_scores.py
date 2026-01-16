"""
Add traffic_score column to roads_circle_vertices.csv
"""

import pandas as pd
import numpy as np
from traffic_scorer_simple import SimpleBramptonTrafficScorer
import time

print("=" * 70)
print("Adding Traffic Scores to roads_circle_vertices.csv")
print("=" * 70)
print()

# Initialize traffic scorer
print("Initializing traffic scorer...")
scorer = SimpleBramptonTrafficScorer()

# Prepare data (build KDTree - this only happens ONCE!)
print("Preparing traffic data (building spatial index)...")
start_setup = time.time()
scorer.prepare_data()
setup_time = time.time() - start_setup
print(f"✓ Setup complete in {setup_time:.2f} seconds")
print()

# Load CSV
print("Loading CSV...")
df = pd.read_csv("roads_circle_vertices.csv")
print(f"✓ Loaded {len(df):,} rows")
print()

# Score coordinates
print("Scoring coordinates...")
coordinates = list(zip(df['lon'], df['lat']))

start_scoring = time.time()
scores = scorer.batch_score(coordinates)
scoring_time = time.time() - start_scoring

# Add traffic_score column
df['traffic_score'] = scores

# Save results
output_file = "roads_circle_vertices.csv"
df.to_csv(output_file, index=False)

print(f"✓ Scored {len(df):,} coordinates in {scoring_time:.2f} seconds")
print(f"  Speed: {len(df)/scoring_time:.0f} coordinates/second")
print()

# Show statistics
print("Traffic Score Statistics:")
print(f"  Min:    {scores.min():.4f}")
print(f"  25th:   {np.percentile(scores, 25):.4f}")
print(f"  Median: {np.median(scores):.4f}")
print(f"  75th:   {np.percentile(scores, 75):.4f}")
print(f"  Max:    {scores.max():.4f}")
print(f"  Mean:   {scores.mean():.4f}")
print()

# Show sample
print("Sample of results:")
print(df.head(10))
print()

print("=" * 70)
print("✓ COMPLETE!")
print(f"Updated file: {output_file}")
print("=" * 70)
