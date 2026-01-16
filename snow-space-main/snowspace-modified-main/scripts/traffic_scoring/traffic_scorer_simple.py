"""
Simplified Brampton Traffic Scorer - Uses only traffic count data for faster setup
No road network download required - perfect for testing
"""

import pickle
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree
from shapely.geometry import Point
from pathlib import Path
from typing import Tuple


class SimpleBramptonTrafficScorer:
    """
    Fast traffic score lookup using only Brampton traffic count data.
    Much faster to set up than the full version (no OSM download).

    Trade-off: Slightly less accurate between measurement points,
    but still very effective for most use cases.
    """

    def __init__(self, data_dir: str = "./brampton_traffic_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.kdtree = None
        self.traffic_points = None
        self.traffic_scores = None

    def prepare_data(self):
        """Load traffic data and build spatial index (fast!)"""

        cache_path = self.data_dir / "simple_scorer_cache.pkl"

        # Try to load from cache
        if cache_path.exists():
            print("Loading from cache...")
            with open(cache_path, 'rb') as f:
                cache = pickle.load(f)
                self.traffic_points = cache['traffic_points']
                self.traffic_scores = cache['traffic_scores']
                self.kdtree = cache['kdtree']
                print(f"✓ Loaded {len(self.traffic_points)} traffic points from cache")
                return

        # Load traffic data
        print("Loading Brampton traffic data...")

        traffic_file = self.data_dir / "brampton_traffic.geojson"

        if not traffic_file.exists():
            print(f"❌ Traffic data not found at {traffic_file}")
            print("Please run: python download_helper.py")
            print("Or manually download from: https://geohub.brampton.ca/datasets/city-of-brampton-traffic-volumes")
            raise FileNotFoundError(f"Traffic data not found: {traffic_file}")

        gdf = gpd.read_file(traffic_file)
        print(f"✓ Loaded {len(gdf)} traffic count locations")

        # Extract coordinates and traffic volumes
        traffic_points_list = []
        traffic_scores_list = []

        for idx, row in gdf.iterrows():
            geom = row.geometry

            if geom is None:
                continue

            # Get coordinates
            if geom.geom_type == 'Point':
                coords = [(geom.x, geom.y)]
            elif geom.geom_type in ['LineString', 'MultiLineString']:
                coords = [geom.centroid.coords[0]]
            else:
                continue

            # Try to find traffic volume field
            # First check for yearly columns (YEAR2023, YEAR2022, etc.)
            volume = None

            # Try recent years first
            year_fields = [f'YEAR{year}' for year in range(2024, 1999, -1)]
            for field in year_fields:
                if field in row.index:
                    try:
                        val = row[field]
                        if pd.notna(val) and val is not None:
                            volume = float(val)
                            if volume > 0:
                                break
                    except (ValueError, TypeError):
                        continue

            # Fallback to other common field names
            if volume is None or volume <= 0:
                for field in ['AADT', 'ADT', 'Volume', 'VOLUME', 'Traffic_Volume', 'Count']:
                    if field in row.index:
                        try:
                            volume = float(row[field])
                            if volume > 0:
                                break
                        except (ValueError, TypeError):
                            continue

            if volume is not None and volume > 0:
                for coord in coords:
                    traffic_points_list.append(coord)
                    traffic_scores_list.append(volume)

        # Convert to numpy arrays
        self.traffic_points = np.array(traffic_points_list)
        traffic_volumes = np.array(traffic_scores_list)

        print(f"✓ Found {len(traffic_volumes)} valid traffic measurements")
        print(f"  Volume range: {traffic_volumes.min():.0f} to {traffic_volumes.max():.0f}")

        # Normalize scores to 0-1 range
        max_traffic = np.percentile(traffic_volumes, 95)
        self.traffic_scores = np.clip(traffic_volumes / max_traffic, 0, 1)

        # Create KD-tree for fast spatial lookups
        print("Building spatial index...")
        self.kdtree = cKDTree(self.traffic_points)

        # Save to cache
        print("Saving to cache...")
        with open(cache_path, 'wb') as f:
            pickle.dump({
                'traffic_points': self.traffic_points,
                'traffic_scores': self.traffic_scores,
                'kdtree': self.kdtree
            }, f)

        print(f"✓ Setup complete! Ready to score coordinates.")

    def get_traffic_score(self, lon: float, lat: float, k: int = 5, max_distance: float = 0.02) -> float:
        """
        Get traffic score for a coordinate.

        Args:
            lon: Longitude
            lat: Latitude
            k: Number of nearest neighbors (default 5)
            max_distance: Max distance to search in degrees (default 0.02 ~= 2km)

        Returns:
            Traffic score from 0 to 1
        """
        if self.kdtree is None:
            raise RuntimeError("Data not prepared. Call prepare_data() first.")

        query_point = np.array([lon, lat])

        # Find k nearest neighbors
        distances, indices = self.kdtree.query(query_point, k=k)

        # If closest point is too far, return 0
        if distances[0] > max_distance:
            return 0.0

        # Inverse distance weighting
        weights = 1.0 / (distances + 1e-6)
        weights = weights / np.sum(weights)

        # Weighted average
        score = np.sum(self.traffic_scores[indices] * weights)

        return float(np.clip(score, 0, 1))

    def batch_score(self, coordinates: list) -> np.ndarray:
        """Score multiple coordinates efficiently"""
        coords_array = np.array(coordinates)
        scores = np.array([
            self.get_traffic_score(lon, lat)
            for lon, lat in coords_array
        ])
        return scores


def main():
    """Example usage"""
    import time

    print("=" * 60)
    print("SIMPLE Brampton Traffic Scorer")
    print("=" * 60)
    print()

    # Initialize scorer
    scorer = SimpleBramptonTrafficScorer()

    # Prepare data (fast - no OSM download!)
    start = time.time()
    scorer.prepare_data()
    elapsed = time.time() - start
    print(f"\n⏱  Setup time: {elapsed:.2f} seconds\n")

    # Test with coordinates
    test_coords = [
        ("Brampton City Hall", -79.7617, 43.6532),
        ("Central Brampton", -79.7, 43.7),
        ("South Brampton", -79.75, 43.65),
        ("East Brampton", -79.65, 43.75),
    ]

    print("=" * 60)
    print("Testing Individual Coordinates")
    print("=" * 60)
    for name, lon, lat in test_coords:
        score = scorer.get_traffic_score(lon, lat)
        print(f"{name:20s} ({lon:.4f}, {lat:.4f}): Score = {score:.3f}")

    # Performance test
    print()
    print("=" * 60)
    print("Performance Test: 30,000 Coordinates")
    print("=" * 60)

    np.random.seed(42)
    n_coords = 30000

    # Generate random coordinates in Brampton
    lons = np.random.uniform(-79.8, -79.6, n_coords)
    lats = np.random.uniform(43.6, 43.8, n_coords)
    coords = list(zip(lons, lats))

    start = time.time()
    scores = scorer.batch_score(coords)
    elapsed = time.time() - start

    print(f"\n✓ Scored {n_coords:,} coordinates in {elapsed:.2f} seconds")
    print(f"  {n_coords/elapsed:.0f} coordinates/second")
    print(f"  {elapsed/n_coords*1000:.2f} ms per coordinate")
    print(f"\nScore distribution:")
    print(f"  Min:    {scores.min():.3f}")
    print(f"  25th:   {np.percentile(scores, 25):.3f}")
    print(f"  Median: {np.median(scores):.3f}")
    print(f"  75th:   {np.percentile(scores, 75):.3f}")
    print(f"  Max:    {scores.max():.3f}")

    print()
    print("=" * 60)
    print("✓ All tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
