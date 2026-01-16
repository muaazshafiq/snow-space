"""
Example usage of BramptonTrafficScorer

This demonstrates how to integrate the traffic scorer into your application.
"""

from traffic_scorer import BramptonTrafficScorer
import time


def example_single_coordinate():
    """Example: Score a single coordinate"""
    print("=== Single Coordinate Scoring ===\n")

    # Initialize the scorer
    scorer = BramptonTrafficScorer(data_dir="./brampton_traffic_data")

    # Prepare data (downloads and caches data - only slow the first time)
    scorer.prepare_data()

    # Get score for a specific location
    lon, lat = -79.7617, 43.6532  # Brampton City Hall area
    score = scorer.get_traffic_score(lon, lat)

    print(f"Location: ({lon}, {lat})")
    print(f"Traffic Score: {score:.3f} (0=lowest, 1=highest traffic)\n")


def example_batch_scoring():
    """Example: Score 30,000 coordinates efficiently"""
    print("=== Batch Scoring 30,000 Coordinates ===\n")

    scorer = BramptonTrafficScorer(data_dir="./brampton_traffic_data")
    scorer.prepare_data()

    # Simulate 30,000 coordinates (replace with your actual coordinates)
    import numpy as np
    np.random.seed(42)

    # Generate coordinates within Brampton bounds
    n_coords = 30000
    coords = [
        (np.random.uniform(-79.8, -79.6), np.random.uniform(43.6, 43.8))
        for _ in range(n_coords)
    ]

    # Score all coordinates
    print(f"Scoring {n_coords} coordinates...")
    start = time.time()

    scores = scorer.batch_score(coords)

    elapsed = time.time() - start

    print(f"✓ Completed in {elapsed:.2f} seconds")
    print(f"  Average: {elapsed/n_coords*1000:.3f} ms per coordinate")
    print(f"  Throughput: {n_coords/elapsed:.0f} coordinates/second")
    print(f"\nScore Statistics:")
    print(f"  Min:  {scores.min():.3f}")
    print(f"  Max:  {scores.max():.3f}")
    print(f"  Mean: {scores.mean():.3f}")
    print(f"  Std:  {scores.std():.3f}\n")


def example_integration_pattern():
    """Example: How to integrate into your application"""
    print("=== Integration Pattern ===\n")

    # Initialize once at application startup
    scorer = BramptonTrafficScorer(data_dir="./brampton_traffic_data")
    scorer.prepare_data()

    # Now you can call get_traffic_score() as many times as needed
    # This is fast because data is cached in memory

    # Example: Process coordinates from a CSV file
    print("Simulating CSV processing...")

    sample_coords = [
        ("Location A", -79.70, 43.70),
        ("Location B", -79.75, 43.65),
        ("Location C", -79.65, 43.75),
        ("Location D", -79.72, 43.68),
    ]

    results = []
    for name, lon, lat in sample_coords:
        score = scorer.get_traffic_score(lon, lat)
        results.append({
            'name': name,
            'lon': lon,
            'lat': lat,
            'traffic_score': score
        })

    print("\nResults:")
    print(f"{'Location':<15} {'Longitude':<12} {'Latitude':<12} {'Traffic Score':<15}")
    print("-" * 60)
    for r in results:
        print(f"{r['name']:<15} {r['lon']:<12.4f} {r['lat']:<12.4f} {r['traffic_score']:<15.3f}")


def example_custom_parameters():
    """Example: Fine-tune the scoring parameters"""
    print("\n=== Custom Parameters ===\n")

    scorer = BramptonTrafficScorer(data_dir="./brampton_traffic_data")
    scorer.prepare_data()

    lon, lat = -79.7617, 43.6532

    # Default parameters
    score_default = scorer.get_traffic_score(lon, lat)

    # Use more neighbors for smoother interpolation
    score_smooth = scorer.get_traffic_score(lon, lat, k=10)

    # Use fewer neighbors for more localized estimates
    score_local = scorer.get_traffic_score(lon, lat, k=3)

    # Adjust maximum search distance
    score_precise = scorer.get_traffic_score(lon, lat, max_distance=0.005)

    print(f"Same location ({lon}, {lat}) with different parameters:")
    print(f"  Default (k=5):           {score_default:.3f}")
    print(f"  Smooth (k=10):           {score_smooth:.3f}")
    print(f"  Local (k=3):             {score_local:.3f}")
    print(f"  Precise (max_dist=0.005): {score_precise:.3f}\n")


if __name__ == "__main__":
    # Run all examples
    example_single_coordinate()
    example_batch_scoring()
    example_integration_pattern()
    example_custom_parameters()

    print("=== All Examples Complete ===")
