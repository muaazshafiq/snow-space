"""
Helper script to download Brampton traffic data

This script tries multiple methods to download the data.
If all fail, it provides clear instructions for manual download.
"""

import requests
import json
from pathlib import Path


def try_download_traffic_data():
    """Try multiple methods to download Brampton traffic data"""

    data_dir = Path("brampton_traffic_data")
    data_dir.mkdir(exist_ok=True)

    print("Brampton Traffic Data Download Helper")
    print("=" * 60)
    print()

    # List of URLs to try
    attempts = [
        {
            'name': 'GeoHub Direct GeoJSON',
            'url': 'https://geohub.brampton.ca/datasets/brampton::city-of-brampton-traffic-volumes.geojson',
        },
        {
            'name': 'ArcGIS Feature Server Query',
            'url': 'https://services1.arcgis.com/pMeXRvgWClLJZr3s/arcgis/rest/services/Traffic_Volumes/FeatureServer/0/query',
            'params': {
                'where': '1=1',
                'outFields': '*',
                'f': 'geojson',
                'returnGeometry': 'true'
            }
        },
        {
            'name': 'Alternative ArcGIS Server',
            'url': 'https://services.arcgis.com/pMeXRvgWClLJZr3s/arcgis/rest/services/Traffic_Volumes/FeatureServer/0/query',
            'params': {
                'where': '1=1',
                'outFields': '*',
                'f': 'geojson'
            }
        }
    ]

    for i, attempt in enumerate(attempts, 1):
        print(f"Attempt {i}/{len(attempts)}: {attempt['name']}")
        print(f"URL: {attempt['url']}")

        try:
            params = attempt.get('params', None)
            response = requests.get(attempt['url'], params=params, timeout=30)

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                # Check if it's valid JSON/GeoJSON
                try:
                    data = response.json()

                    # Check if it has features (GeoJSON format)
                    if 'features' in data:
                        print(f"✓ Success! Found {len(data['features'])} features")

                        # Save to file
                        output_file = data_dir / "brampton_traffic.geojson"
                        with open(output_file, 'w') as f:
                            json.dump(data, f)

                        print(f"✓ Saved to: {output_file}")
                        print(f"\nYou can now run: python traffic_scorer.py")
                        return True
                    else:
                        print(f"✗ Response is JSON but not GeoJSON format")
                        print(f"Keys found: {list(data.keys())}")

                except json.JSONDecodeError:
                    print(f"✗ Response is not valid JSON")
                    print(f"Response preview: {response.text[:200]}...")

            else:
                print(f"✗ Failed with status code {response.status_code}")

                # Try to show error message
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        print(f"Error message: {error_data['error']}")
                except:
                    pass

        except Exception as e:
            print(f"✗ Error: {e}")

        print()

    # All attempts failed
    print("=" * 60)
    print("ALL AUTOMATIC DOWNLOAD ATTEMPTS FAILED")
    print("=" * 60)
    print()
    print("Please download manually:")
    print()
    print("1. Visit: https://geohub.brampton.ca/datasets/city-of-brampton-traffic-volumes")
    print()
    print("2. Look for Download button (usually top-right)")
    print("   OR look for 'APIs' or 'View API Resources' tab")
    print()
    print("3. Download as GeoJSON or CSV format")
    print()
    print(f"4. Save to: {data_dir.absolute()}/brampton_traffic.geojson")
    print("   (or brampton_traffic.csv)")
    print()
    print("5. Then run: python traffic_scorer.py")
    print()
    print("=" * 60)

    # Let's also check what's available at the main page
    print()
    print("Checking main dataset page...")
    try:
        response = requests.get('https://geohub.brampton.ca/datasets/city-of-brampton-traffic-volumes', timeout=10)
        if response.status_code == 200:
            # Look for common download link patterns in the HTML
            if 'download' in response.text.lower():
                print("✓ Page accessible - download button should be available")
            if 'arcgis.com' in response.text:
                # Try to extract the server URL
                import re
                servers = re.findall(r'https://services\d*\.arcgis\.com/[^"\']+/FeatureServer/\d+', response.text)
                if servers:
                    print(f"\nFound potential API endpoints:")
                    for server in set(servers):
                        print(f"  - {server}")
                        print(f"    Try: {server}/query?where=1=1&outFields=*&f=geojson")
    except Exception as e:
        print(f"Could not check main page: {e}")

    return False


if __name__ == "__main__":
    success = try_download_traffic_data()

    if not success:
        print("\n" + "=" * 60)
        print("TIP: You can also try using just OpenStreetMap data")
        print("It will be less accurate but will work without Brampton data")
        print("=" * 60)
