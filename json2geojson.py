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

# --- CACHE SYSTEM ---
CACHE_FILE = "geocoding_cache.json"
ADDRESS_CACHE = {}

def load_cache():
    global ADDRESS_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                ADDRESS_CACHE = json.load(f)
        except Exception:
            ADDRESS_CACHE = {}

def save_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(ADDRESS_CACHE, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"\n⚠️ Warning: Failed to save cache: {e}")

def get_place_name(lat, lng):
    # Use 5 decimal places for caching (approx 1 meter precision)
    cache_key = f"{lat:.5f},{lng:.5f}"
    
    if cache_key in ADDRESS_CACHE:
        return ADDRESS_CACHE[cache_key]

    try:
        # Respect Nominatim's 1 second limit only if we actually hit the API
        time.sleep(1) 
        location = geolocator.reverse((lat, lng), timeout=10)
        address = location.address if location else f"Coordinates ({lat}, {lng})"
        
        # Save to cache
        ADDRESS_CACHE[cache_key] = address
        save_cache()
        return address
    except (GeocoderServiceError, Exception):
        return f"Coordinates ({lat}, {lng})"
# --- END CACHE SYSTEM ---

def clean_and_parse_coordinates(lat_lng_str):
    if not lat_lng_str:
        return None
    cleaned = lat_lng_str.replace("°", "")
    try:
        lat_str, lng_str = cleaned.split(",")
        return [float(lng_str.strip()), float(lat_str.strip())]
    except ValueError:
        return None

def print_progress(current, total, prefix='', suffix='', length=30):
    """Simple text-based progress bar"""
    if total <= 0: return
    percent = ("{0:.1f}").format(100 * (current / float(total)))
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()

def process_segments(segments, data_by_year, specific_mode, total_size=None, f_obj=None):
    count = 0
    is_list = isinstance(segments, list)
    total_count = len(segments) if is_list else None

    for segment in segments:
        count += 1
        if not segment or not isinstance(segment, dict): continue
        
        # Update Progress Bar
        if total_size and f_obj:
            current_pos = f_obj.tell()
            print_progress(current_pos, total_size, prefix='Progress:', suffix='Complete')
        elif total_count:
            print_progress(count, total_count, prefix='Progress:', suffix='Complete')

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
                    # Clear line for the log
                    sys.stdout.write('\r' + ' ' * 100 + '\r')
                    print(f"📍 [{year}] Found: {address[:70]}...")
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
    
    if total_size: print_progress(total_size, total_size, prefix='Progress:', suffix='Complete')
    elif total_count: print_progress(total_count, total_count, prefix='Progress:', suffix='Complete')
    print()

def main():
    print("\n=== Semantic JSON to Yearly/Specific GeoJSON ===")
    print(" (Enter '0' or 'back' to return to Master Menu)\n")
    load_cache()
    
    if not HAS_IJSON:
        print("⚠️  Warning: 'ijson' library not found. Falling back to standard 'json' library.")
        print("    Large files might cause memory errors. Install it using: pip install ijson\n")

    # 1. Input source JSON filename
    while True:
        try:
            input_filename = input("Enter source JSON filename: ").strip()
            if input_filename.lower() in ['0', 'back', 'b']: return
            if os.path.exists(input_filename):
                break
            print(f"Error: File '{input_filename}' not found.\n")
        except KeyboardInterrupt:
            return

    # 2. SELECT YEAR CONVERSION MODE MENU
    specific_mode = None
    try:
        print("\nSelect Year Conversion Mode:")
        print(" [1] Complete Conversion (All years separated automatically)")
        print(" [2] Specific Year Conversion Only (Example: 2025)")
        print(" [0] Back to Master Menu")

        while True:
            mode_choice = input("Enter choice: ").strip()
            if mode_choice in ['0', 'back', 'b']: return
            if mode_choice == "1":
                print("-> Active Mode: Complete conversion for all years.\n")
                break
            elif mode_choice == "2":
                while True:
                    specific_mode = input("Enter year to convert (or '0' for back): ").strip()
                    if specific_mode in ['0', 'back', 'b']: return
                    if specific_mode.isdigit() and len(specific_mode) == 4:
                        break
                    print("❌ Error: Year format must be 4 digits (Example: 2025).")
                print(f"-> Active Mode: Only processing data for year {specific_mode}.\n")
                break
            else:
                print("❌ Invalid choice! Please enter either 1 or 2.")
    except KeyboardInterrupt:
        return

    # 3. Input file prefix
    try:
        base_prefix = input("Enter prefix for output filenames (default: output, '0' for back): ").strip()
        if base_prefix in ['0', 'back', 'b']: return
        if not base_prefix: base_prefix = "output"
        if base_prefix.endswith(".geojson"): base_prefix = base_prefix[:-8]
    except KeyboardInterrupt:
        return

    data_by_year = {}

    try:
        print("\n⏳ Processing coordinates... (Press Ctrl+C anytime to stop & save partial results)")
        
        if HAS_IJSON:
            file_size = os.path.getsize(input_filename)
            with open(input_filename, 'rb') as f:
                segments = ijson.items(f, 'semanticSegments.item', use_float=True)
                process_segments(segments, data_by_year, specific_mode, total_size=file_size, f_obj=f)
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
            
            print("\n✅ All conversions complete.")
        else:
            print("\n❌ No data processed based on your selection criteria.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
