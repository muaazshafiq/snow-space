"""
Brampton Traffic Scorer - Fast coordinate-based traffic score lookup system
Uses hybrid approach: actual traffic counts + OSM road network + spatial interpolation
"""

import os
import pickle
import requests
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.interpolate import RBFInterpolator
from scipy.spatial import cKDTree
from shapely.geometry import Point
import osmnx as ox
from pathlib import Path
from typing import Tuple, Optional


class BramptonTrafficScorer:
    """
    Fast traffic score lookup for Brampton coordinates.

    Downloads data once, then provides O(log n) lookups using spatial indexing.
    Scores range from 0 (lowest traffic) to 1 (highest traffic).
    """

    def __init__(self, data_dir: str = "./data"):
        """
        Initialize the traffic scorer.

        Args:
            data_dir: Directory to store downloaded data and cache
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.traffic_data = None
        self.road_network = None
        self.kdtree = None
        self.traffic_points = None
        self.traffic_scores = None
        self.interpolator = None

        # Brampton bounding box (approximate)
        self.brampton_bounds = {
            'north': 43.8,
            'south': 43.6,
            'east': -79.6,
            'west': -79.8
        }

    def download_traffic_data(self) -> gpd.GeoDataFrame:
        """
        Download Brampton traffic volume data from GeoHub.
        If automatic download fails, falls back to manual file loading.

        Returns:
            GeoDataFrame with traffic count data
        """
        # First, check if user has manually placed a file
        manual_files = [
            self.data_dir / "brampton_traffic.geojson",
            self.data_dir / "brampton_traffic.csv",
            self.data_dir / "City_of_Brampton_Traffic_Volumes.geojson",
            self.data_dir / "City_of_Brampton_Traffic_Volumes.csv",
        ]

        for manual_file in manual_files:
            if manual_file.exists():
                print(f"Found manually downloaded file: {manual_file.name}")
                try:
                    if manual_file.suffix == '.csv':
                        # Load CSV and convert to GeoDataFrame
                        df = pd.read_csv(manual_file)
                        # Try to find lat/lon columns
                        lat_col = next((c for c in df.columns if c.lower() in ['latitude', 'lat', 'y']), None)
                        lon_col = next((c for c in df.columns if c.lower() in ['longitude', 'lon', 'long', 'x']), None)
                        if lat_col and lon_col:
                            geometry = [Point(xy) for xy in zip(df[lon_col], df[lat_col])]
                            gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
                            print(f"Loaded {len(gdf)} traffic count locations from CSV")
                            return gdf
                    else:
                        gdf = gpd.read_file(manual_file)
                        print(f"Loaded {len(gdf)} traffic count locations from {manual_file.suffix}")
                        return gdf
                except Exception as e:
                    print(f"Error loading manual file {manual_file.name}: {e}")
                    continue

        print("No manual file found. Attempting to download...")

        # Try multiple download methods
        download_attempts = [
            # Method 1: Direct GeoJSON from GeoHub (VERIFIED WORKING!)
            {
                'url': 'https://geohub.brampton.ca/datasets/brampton::city-of-brampton-traffic-volumes.geojson',
                'method': 'direct'
            },
            # Method 2: ArcGIS Feature Server
            {
                'url': 'https://services1.arcgis.com/pMeXRvgWClLJZr3s/arcgis/rest/services/Traffic_Volumes/FeatureServer/0/query',
                'method': 'api',
                'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'returnGeometry': 'true'}
            },
        ]

        for i, attempt in enumerate(download_attempts, 1):
            try:
                print(f"Download attempt {i}/{len(download_attempts)}...")

                if attempt['method'] == 'direct':
                    gdf = gpd.read_file(attempt['url'])
                elif attempt['method'] == 'api':
                    # Use requests for API calls with parameters
                    response = requests.get(attempt['url'], params=attempt.get('params', {}), timeout=60)
                    response.raise_for_status()
                    # Save temporarily and load with geopandas
                    temp_path = self.data_dir / "temp_traffic.geojson"
                    with open(temp_path, 'w') as f:
                        f.write(response.text)
                    gdf = gpd.read_file(temp_path)
                    temp_path.unlink()  # Delete temp file
                else:
                    continue

                # Save for future use
                save_path = self.data_dir / "brampton_traffic.geojson"
                gdf.to_file(save_path, driver='GeoJSON')
                print(f"✓ Downloaded {len(gdf)} traffic count locations")
                return gdf

            except Exception as e:
                print(f"  Attempt {i} failed: {e}")
                continue

        # If all downloads fail, provide manual download instructions
        print("\n" + "="*70)
        print("AUTOMATIC DOWNLOAD FAILED")
        print("="*70)
        print("\nPlease manually download the traffic data:")
        print("\n1. Visit: https://geohub.brampton.ca/datasets/city-of-brampton-traffic-volumes")
        print("2. Click the 'Download' button")
        print("3. Choose GeoJSON or CSV format")
        print(f"4. Save the file to: {self.data_dir.absolute()}/")
        print("5. Name it: brampton_traffic.geojson (or .csv)")
        print("6. Run this script again")
        print("\nAlternatively, you can:")
        print("- Right-click on the dataset page")
        print("- Look for 'View API Resources' or 'APIs' tab")
        print("- Copy the GeoJSON URL and download it manually")
        print("="*70 + "\n")

        raise Exception("Could not download traffic data automatically. Please download manually (see instructions above).")

    def download_road_network(self) -> gpd.GeoDataFrame:
        """
        Download OpenStreetMap road network for Brampton.

        Returns:
            GeoDataFrame with road network
        """
        print("Downloading OpenStreetMap road network for Brampton...")

        cache_path = self.data_dir / "brampton_roads.pkl"

        if cache_path.exists():
            print("Loading cached road network...")
            with open(cache_path, 'rb') as f:
                return pickle.load(f)

        try:
            # Download road network using OSMnx (v2.x API)
            # In OSMnx 2.x, use bbox parameter as tuple (north, south, east, west)
            G = ox.graph_from_bbox(
                bbox=(
                    self.brampton_bounds['north'],
                    self.brampton_bounds['south'],
                    self.brampton_bounds['east'],
                    self.brampton_bounds['west']
                ),
                network_type='drive'
            )

            # Convert to GeoDataFrame
            roads = ox.graph_to_gdfs(G, nodes=False)

            # Cache the result
            with open(cache_path, 'wb') as f:
                pickle.dump(roads, f)

            print(f"Downloaded {len(roads)} road segments")
            return roads

        except Exception as e:
            print(f"Error downloading road network: {e}")
            raise

    def prepare_data(self):
        """
        Download and prepare all data for fast lookups.
        Creates spatial index and interpolation function.
        """
        cache_path = self.data_dir / "scorer_cache.pkl"

        # Try to load from cache
        if cache_path.exists():
            print("Loading from cache...")
            with open(cache_path, 'rb') as f:
                cache = pickle.load(f)
                self.traffic_points = cache['traffic_points']
                self.traffic_scores = cache['traffic_scores']
                self.kdtree = cache['kdtree']
                print("Loaded from cache successfully!")
                return

        # Download traffic data
        self.traffic_data = self.download_traffic_data()

        # Download road network
        self.road_network = self.download_road_network()

        # Process traffic data
        print("Processing traffic data...")
        traffic_points_list = []
        traffic_scores_list = []

        # Extract coordinates and traffic volumes from traffic data
        for idx, row in self.traffic_data.iterrows():
            geom = row.geometry

            if geom is None:
                continue

            # Get coordinates (handle both Point and LineString geometries)
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

        # Add road network data with estimated traffic based on road type
        print("Adding road network traffic estimates...")
        road_type_scores = {
            'motorway': 50000,
            'trunk': 40000,
            'primary': 30000,
            'secondary': 20000,
            'tertiary': 10000,
            'residential': 2000,
            'unclassified': 5000
        }

        for idx, road in self.road_network.iterrows():
            centroid = road.geometry.centroid

            # Get road type
            highway_type = road.get('highway', 'unclassified')
            if isinstance(highway_type, list):
                highway_type = highway_type[0]

            # Assign estimated traffic based on road type
            estimated_traffic = road_type_scores.get(highway_type, 5000)

            traffic_points_list.append((centroid.x, centroid.y))
            traffic_scores_list.append(estimated_traffic)

        # Convert to numpy arrays
        self.traffic_points = np.array(traffic_points_list)
        traffic_volumes = np.array(traffic_scores_list)

        # Normalize scores to 0-1 range
        print("Normalizing traffic scores...")
        max_traffic = np.percentile(traffic_volumes, 95)  # Use 95th percentile to avoid outliers
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

        print(f"Preparation complete! Indexed {len(self.traffic_points)} points")

    def get_traffic_score(self, lon: float, lat: float, k: int = 5, max_distance: float = 0.01) -> float:
        """
        Get traffic score for a given coordinate using k-nearest neighbors interpolation.

        Args:
            lon: Longitude
            lat: Latitude
            k: Number of nearest neighbors to use for interpolation
            max_distance: Maximum distance (in degrees) to search for neighbors

        Returns:
            Traffic score from 0 (lowest) to 1 (highest)
        """
        if self.kdtree is None:
            raise RuntimeError("Data not prepared. Call prepare_data() first.")

        query_point = np.array([lon, lat])

        # Find k nearest neighbors
        distances, indices = self.kdtree.query(query_point, k=k)

        # If all points are too far away, return 0
        if distances[0] > max_distance:
            return 0.0

        # Use inverse distance weighting
        # Add small epsilon to avoid division by zero
        weights = 1.0 / (distances + 1e-6)
        weights = weights / np.sum(weights)  # Normalize weights

        # Calculate weighted average of traffic scores
        score = np.sum(self.traffic_scores[indices] * weights)

        return float(np.clip(score, 0, 1))

    def batch_score(self, coordinates: list) -> np.ndarray:
        """
        Score multiple coordinates efficiently.

        Args:
            coordinates: List of (lon, lat) tuples

        Returns:
            Array of traffic scores
        """
        coords_array = np.array(coordinates)
        scores = np.array([
            self.get_traffic_score(lon, lat)
            for lon, lat in coords_array
        ])
        return scores


def main():
    """Example usage"""
    # Initialize scorer
    scorer = BramptonTrafficScorer(data_dir="./brampton_traffic_data")

    # Download and prepare data (only needs to be done once)
    scorer.prepare_data()

    # Test with a few coordinates in Brampton
    test_coords = [
        (-79.7, 43.7),   # Central Brampton
        (-79.75, 43.65), # South Brampton
        (-79.65, 43.75)  # East Brampton
    ]

    print("\n=== Testing Traffic Scores ===")
    for lon, lat in test_coords:
        score = scorer.get_traffic_score(lon, lat)
        print(f"Coordinate ({lon}, {lat}): Traffic Score = {score:.3f}")

    # Batch scoring example
    print("\n=== Batch Scoring Example ===")
    import time

    # Generate random coordinates in Brampton
    np.random.seed(42)
    n_coords = 1000
    lons = np.random.uniform(-79.8, -79.6, n_coords)
    lats = np.random.uniform(43.6, 43.8, n_coords)
    coords = list(zip(lons, lats))

    start = time.time()
    scores = scorer.batch_score(coords)
    elapsed = time.time() - start

    print(f"Scored {n_coords} coordinates in {elapsed:.3f} seconds")
    print(f"Average time per coordinate: {elapsed/n_coords*1000:.3f} ms")
    print(f"Score statistics: min={scores.min():.3f}, max={scores.max():.3f}, mean={scores.mean():.3f}")


if __name__ == "__main__":
    main()
