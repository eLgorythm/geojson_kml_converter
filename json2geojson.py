import json
import os
import time
import sys
import subprocess
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
        return location.address if location else f"Koordinat ({lat}, {lng})"
    except (GeocoderServiceError, Exception):
        return f"Koordinat ({lat}, {lng})"

def tawarkan_konversi_kml(geojson_file):
    """Fungsi interaktif untuk memanggil script KML terpisah"""
    print("\n------------------------------------------------")
    try:
        pilihan = input("Apakah Anda mau mengonversi hasil GeoJSON tadi ke format KML? (y/n): ").strip().lower()
        if pilihan in ['y', 'yes', 'ya']:
            print(f"⏳ Menjalankan script terpisah 'geojson_to_kml.py' dengan sumber: {geojson_file}...")
            # Menjalankan script terpisah menggunakan subprocess dan melempar nama file GeoJSON sebagai parameter
            subprocess.run([sys.executable, "geojson2kml.py", geojson_file])
        else:
            print("Konversi KML dilewati.")
    except KeyboardInterrupt:
        print("\n[!] Pembatalan opsi KML.")

def main():
    print("=== Semantic JSON to Single GeoJSON ===")
    
    while True:
        try:
            input_filename = input("Masukkan nama file JSON sumber (contoh: data.json): ").strip()
            if os.path.exists(input_filename):
                break
            print(f"Error: File '{input_filename}' tidak ditemukan.\n")
        except KeyboardInterrupt:
            print("\n\n[!] Program ditutup.")
            sys.exit(0)

    try:
        output_filename = input("Masukkan nama file GeoJSON hasil (default: output.geojson): ").strip()
        if not output_filename: output_filename = "output.geojson"
        if not output_filename.endswith(".geojson"): output_filename += ".geojson"
    except KeyboardInterrupt:
        print("\n\n[!] Program ditutup.")
        sys.exit(0)

    features_lengkap = []
    interrupted = False

    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        segments = source_data.get("semanticSegments", []) if isinstance(source_data, dict) else source_data

        print("\n⏳ Memproses koordinat... (Tekan Ctrl+C kapan saja untuk stop & simpan seadanya)")

        for segment in segments:
            if not segment or not isinstance(segment, dict): continue
            start_time, end_time = segment.get("startTime"), segment.get("endTime")
            
            try:
                if "visit" in segment:
                    visit_data = segment["visit"]
                    top_candidate = visit_data.get("topCandidate", {})
                    coords = clean_and_parse_coordinates(top_candidate.get("placeLocation", {}).get("latLng"))
                    if coords:
                        lng, lat = coords
                        nama_alamat = get_place_name(lat, lng)
                        print(f"📍 Alamat ketemu: {nama_alamat[:50]}...")
                        features_lengkap.append({
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": coords},
                            "properties": {
                                "name": nama_alamat, "Tipe": "Kunjungan Tempat",
                                "Waktu Mulai": start_time, "Waktu Selesai": end_time,
                                "Place ID": top_candidate.get("placeId")
                            }
                        })

                elif "activity" in segment:
                    activity_data = segment["activity"]
                    start_coords = clean_and_parse_coordinates(activity_data.get("start", {}).get("latLng"))
                    end_coords = clean_and_parse_coordinates(activity_data.get("end", {}).get("latLng"))
                    if start_coords and end_coords:
                        act_type = activity_data.get("topCandidate", {}).get('type', 'PERJALANAN')
                        features_lengkap.append({
                            "type": "Feature",
                            "geometry": {"type": "LineString", "coordinates": [start_coords, end_coords]},
                            "properties": {
                                "name": f"Rute Perjalanan ({act_type})", "Tipe": f"Perjalanan ({act_type})",
                                "Waktu Mulai": start_time, "Waktu Selesai": end_time,
                                "Jarak (Meter)": activity_data.get("distanceMeters")
                            }
                        })

                elif "timelinePath" in segment:
                    path_points = segment["timelinePath"]
                    line_coordinates = [clean_and_parse_coordinates(p.get("point")) for p in path_points if clean_and_parse_coordinates(p.get("point"))]
                    if len(line_coordinates) > 1:
                        features_lengkap.append({
                            "type": "Feature",
                            "geometry": {"type": "LineString", "coordinates": line_coordinates},
                            "properties": {"name": "Jalur Detail", "Tipe": "Rute Jalan Detail", "Waktu Mulai": start_time, "Waktu Selesai": end_time}
                        })

            except KeyboardInterrupt:
                print("\n\n⚠️ Dihentikan paksa oleh user (Ctrl+C)!")
                interrupted = True
                break

        # Sesi Menyimpan File GeoJSON (Akan selalu jalan baik selesai normal maupun cancel)
        if features_lengkap:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump({"type": "FeatureCollection", "features": features_lengkap}, f, indent=2, ensure_ascii=False)
            print(f"\n Sukses! Berhasil mengamankan {len(features_lengkap)} data ke '{output_filename}'")
            
            # Pemicu tawaran KML otomatis menggunakan file output tadi
            tawarkan_konversi_kml(output_filename)
        else:
            print("\n❌ Tidak ada data yang berhasil diproses.")

    except Exception as e:
        print(f"Terjadi kesalahan: {str(e)}")

if __name__ == "__main__":
    main()
