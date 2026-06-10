import json
import os
import time
import sys
import subprocess

# Try to import ijson for large file support, fallback to standard json
try:
    import ijson
    HAS_IJSON = True
except ImportError:
    HAS_IJSON = False

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError

geolocator = Nominatim(user_agent="semantic_geojson_namer_v8")

def clean_and_parse_coordinates(lat_lng_str):
    if not lat_lng_str:
        return None
    cleaned = lat_lng_str.replace("°", "")
    try:
        lat_str, lng_str = cleaned.split(",")
        return [float(lng_str.strip()), float(lat_str.strip())]
    except ValueError:
        return None

def get_place_name(lat, lng):
    try:
        time.sleep(1) 
        location = geolocator.reverse((lat, lng), timeout=10)
        return location.address if location else f"Coordinates ({lat}, {lng})"
    except (GeocoderServiceError, Exception):
        return f"Coordinates ({lat}, {lng})"

def offer_kml_conversion(geojson_file_list):
    """Interactive function to call a separate KML script for each GeoJSON file"""
    print("\n------------------------------------------------")
    try:
        choice = input("Do you want to convert the GeoJSON results to KML format? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            for geojson_file in geojson_file_list:
                if os.path.exists(geojson_file):
                    print(f"⏳ Running separate script 'geojson2kml.py' with source: {geojson_file}...")
                    subprocess.run([sys.executable, "geojson2kml.py", geojson_file])
        else:
            print("KML conversion skipped.")
    except KeyboardInterrupt:
        print("\n[!] KML option cancelled.")

def offer_visualization(geojson_file_list):
    """Interactive function to offer visualization after conversion"""
    print("\n------------------------------------------------")
    try:
        choice = input("Do you want to visualize the results in a web browser? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            for geojson_file in geojson_file_list:
                if os.path.exists(geojson_file):
                    print(f"⏳ Running 'visualizer.py' for: {geojson_file}...")
                    # Note: visualizer.py currently takes input via prompts, 
                    # we might need to modify it slightly for auto-run or just let it prompt.
                    subprocess.run([sys.executable, "visualizer.py"], input=f"1\n", text=True)
        else:
            print("Visualization skipped.")
    except KeyboardInterrupt:
        print("\n[!] Visualization option cancelled.")

def main():
    print("=== Semantic JSON to Yearly/Specific GeoJSON ===")
    
    if not HAS_IJSON:
        print("⚠️  Warning: 'ijson' library not found. Falling back to standard 'json' library.")
        print("    Large files might cause memory errors. Install it using: pip install ijson\n")

    # 1. Input source JSON filename
    while True:
        try:
            input_filename = input("Enter source JSON filename (example: data.json): ").strip()
            if os.path.exists(input_filename):
                break
            print(f"Error: File '{input_filename}' not found.\n")
        except KeyboardInterrupt:
            print("\n\n[!] Program closed.")
            sys.exit(0)

    # 2. SELECT YEAR CONVERSION MODE MENU
    specific_mode = None
    try:
        print("\nSelect Year Conversion Mode:")
        print(" [1] Complete Conversion (All years separated automatically)")
        print(" [2] Specific Year Conversion Only (Example: 2025)")

        while True:
            mode_choice = input("Enter choice (1/2): ").strip()
            if mode_choice == "1":
                print("-> Active Mode: Complete conversion for all years.\n")
                break
            elif mode_choice == "2":
                while True:
                    specific_mode = input("Enter year to convert (example: 2025): ").strip()
                    if specific_mode.isdigit() and len(specific_mode) == 4:
                        break
                    print("❌ Error: Year format must be 4 digits (Example: 2025).")
                print(f"-> Active Mode: Only processing data for year {specific_mode}.\n")
                break
            else:
                print("❌ Invalid choice! Please enter either 1 or 2.")
    except KeyboardInterrupt:
        print("\n\n[!] Program closed.")
        sys.exit(0)

    # 3. Input file prefix
    try:
        base_prefix = input("Enter prefix for output GeoJSON filenames (default: output): ").strip()
        if not base_prefix: base_prefix = "output"
        if base_prefix.endswith(".geojson"): base_prefix = base_prefix[:-8]
    except KeyboardInterrupt:
        print("\n\n[!] Program closed.")
        sys.exit(0)

    data_by_year = {}

    try:
        print("\n⏳ Processing coordinates... (Press Ctrl+C anytime to stop & save partial results)")
        
        # Use ijson if available for streaming large files
        if HAS_IJSON:
            with open(input_filename, 'rb') as f:
                # Support both structures: {"semanticSegments": [...]} or just [...]
                segments = ijson.items(f, 'semanticSegments.item')
                process_segments(segments, data_by_year, specific_mode)
        else:
            with open(input_filename, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
                segments = source_data.get("semanticSegments", []) if isinstance(source_data, dict) else source_data
                process_segments(segments, data_by_year, specific_mode)

        # Saving GeoJSON files by year
        created_files = []
        if data_by_year:
            print("\n⏳ Saving data to yearly files...")
            for year, feature_list in data_by_year.items():
                if not feature_list: continue
                yearly_output_file = f"{base_prefix}_{year}.geojson"
                with open(yearly_output_file, 'w', encoding='utf-8') as f:
                    json.dump({"type": "FeatureCollection", "features": feature_list}, f, indent=2, ensure_ascii=False)
                print(f" -> Successfully saved {len(feature_list)} features to '{yearly_output_file}'")
                created_files.append(yearly_output_file)
        else:
            print("\n❌ No data processed based on your selection criteria.")

        # Automation prompts
        if created_files:
            offer_kml_conversion(created_files)
            offer_visualization(created_files)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def process_segments(segments, data_by_year, specific_mode):
    for segment in segments:
        if not segment or not isinstance(segment, dict): continue
        start_time = segment.get("startTime")
        end_time = segment.get("endTime")
        
        if start_time and len(start_time) >= 4:
            year = start_time[:4]
        else:
            year = "Unknown"

        if specific_mode and year != specific_mode:
            continue

        if year not in data_by_year:
            data_by_year[year] = []
        
        try:
            if "visit" in segment:
                visit_data = segment["visit"]
                top_candidate = visit_data.get("topCandidate", {})
                coords = clean_and_parse_coordinates(top_candidate.get("placeLocation", {}).get("latLng"))
                if coords:
                    lng, lat = coords
                    address = get_place_name(lat, lng)
                    print(f"📍 [{year}] Address found: {address}")
                    data_by_year[year].append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": coords},
                        "properties": {
                            "name": address, "Type": "Place Visit",
                            "Start Time": start_time, "End Time": end_time,
                            "Place ID": top_candidate.get("placeId")
                        }
                    })

            elif "activity" in segment:
                activity_data = segment["activity"]
                start_coords = clean_and_parse_coordinates(activity_data.get("start", {}).get("latLng"))
                end_coords = clean_and_parse_coordinates(activity_data.get("end", {}).get("latLng"))
                if start_coords and end_coords:
                    act_type = activity_data.get("topCandidate", {}).get('type', 'TRAVEL')
                    data_by_year[year].append({
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": [start_coords, end_coords]},
                        "properties": {
                            "name": f"Travel Route ({act_type})", "Type": f"Travel ({act_type})",
                            "Start Time": start_time, "End Time": end_time,
                            "Distance (Meters)": activity_data.get("distanceMeters")
                        }
                    })

            elif "timelinePath" in segment:
                path_points = segment["timelinePath"]
                line_coordinates = [clean_and_parse_coordinates(p.get("point")) for p in path_points if clean_and_parse_coordinates(p.get("point"))]
                if len(line_coordinates) > 1:
                    data_by_year[year].append({
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": line_coordinates},
                        "properties": {"name": "Detail Path", "Type": "Detailed Route", "Start Time": start_time, "End Time": end_time}
                    })

        except KeyboardInterrupt:
            print("\n\n⚠️ Forcefully stopped by user (Ctrl+C)!")
            break

if __name__ == "__main__":
    main()
