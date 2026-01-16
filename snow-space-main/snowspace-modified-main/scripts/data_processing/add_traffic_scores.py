"""
Add traffic_score column to ontario_roads_vertices_wgs84.csv
Processes the CSV in chunks for memory efficiency
"""

import pandas as pd
import numpy as np
from traffic_scorer_simple import SimpleBramptonTrafficScorer
import time

def add_traffic_scores_to_csv(
    input_csv: str = "ontario_roads_vertices_wgs84.csv",
    output_csv: str = "ontario_roads_vertices_wgs84_scored.csv",
    chunk_size: int = 10000
):
    """
    Add traffic_score column to CSV file.

    Args:
        input_csv: Path to input CSV file
        output_csv: Path to output CSV file
        chunk_size: Number of rows to process at once (for memory efficiency)
    """

    print("=" * 70)
    print("Adding Traffic Scores to CSV")
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

    # Get total number of rows for progress tracking
    print(f"Counting rows in {input_csv}...")
    total_rows = sum(1 for _ in open(input_csv)) - 1  # -1 for header
    print(f"✓ Found {total_rows:,} rows to process")
    print()

    # Process CSV in chunks
    print("Processing CSV in chunks...")
    print(f"Chunk size: {chunk_size:,} rows")
    print()

    first_chunk = True
    rows_processed = 0
    start_scoring = time.time()

    for chunk_idx, chunk in enumerate(pd.read_csv(input_csv, chunksize=chunk_size)):
        chunk_start = time.time()

        # Get traffic scores for this chunk
        coordinates = list(zip(chunk['lon'], chunk['lat']))
        scores = scorer.batch_score(coordinates)

        # Add traffic_score column
        chunk['traffic_score'] = scores

        # Write to output CSV
        mode = 'w' if first_chunk else 'a'
        header = first_chunk
        chunk.to_csv(output_csv, mode=mode, header=header, index=False)

        rows_processed += len(chunk)
        chunk_time = time.time() - chunk_start
        rows_per_sec = len(chunk) / chunk_time

        # Progress update
        progress_pct = (rows_processed / total_rows) * 100
        elapsed = time.time() - start_scoring
        eta = (elapsed / rows_processed) * (total_rows - rows_processed)

        print(f"Chunk {chunk_idx + 1}: {rows_processed:,}/{total_rows:,} rows "
              f"({progress_pct:.1f}%) | "
              f"{rows_per_sec:.0f} rows/sec | "
              f"ETA: {eta:.0f}s")

        first_chunk = False

    total_time = time.time() - start_scoring

    print()
    print("=" * 70)
    print("✓ COMPLETE!")
    print("=" * 70)
    print(f"Setup time:      {setup_time:.2f} seconds (one-time cost)")
    print(f"Scoring time:    {total_time:.2f} seconds")
    print(f"Total time:      {setup_time + total_time:.2f} seconds")
    print(f"Rows processed:  {rows_processed:,}")
    print(f"Average speed:   {rows_processed/total_time:.0f} rows/second")
    print(f"Time per row:    {total_time/rows_processed*1000:.2f} ms")
    print()
    print(f"Output saved to: {output_csv}")
    print("=" * 70)


def main():
    """Run the script"""

    # Check if input file exists
    input_file = "ontario_roads_vertices_wgs84.csv"

    import os
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found!")
        return

    # Run the processing
    add_traffic_scores_to_csv(
        input_csv=input_file,
        output_csv="ontario_roads_vertices_wgs84_scored.csv",
        chunk_size=10000  # Adjust this if you have memory constraints
    )

    # Show a sample of the results
    print()
    print("Sample of results:")
    print()
    df_sample = pd.read_csv("ontario_roads_vertices_wgs84_scored.csv", nrows=10)
    print(df_sample)


if __name__ == "__main__":
    main()
