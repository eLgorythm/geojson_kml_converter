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

def tawarkan_konversi_kml(daftar_file_geojson):
    """Fungsi interaktif untuk memanggil script KML terpisah bagi setiap berkas GeoJSON"""
    print("\n------------------------------------------------")
    try:
        pilihan = input("Apakah Anda mau mengonversi hasil GeoJSON tadi ke format KML? (y/n): ").strip().lower()
        if pilihan in ['y', 'yes', 'ya']:
            for geojson_file in daftar_file_geojson:
                if os.path.exists(geojson_file):
                    print(f"⏳ Menjalankan script terpisah 'geojson2kml.py' dengan sumber: {geojson_file}...")
                    subprocess.run([sys.executable, "geojson2kml.py", geojson_file])
        else:
            print("Konversi KML dilewati.")
    except KeyboardInterrupt:
        print("\n[!] Pembatalan opsi KML.")

def main():
    print("=== Semantic JSON to Yearly/Specific GeoJSON ===")
    
    # 1. Input nama file sumber JSON
    while True:
        try:
            input_filename = input("Masukkan nama file JSON sumber (contoh: data.json): ").strip()
            if os.path.exists(input_filename):
                break
            print(f"Error: File '{input_filename}' tidak ditemukan.\n")
        except KeyboardInterrupt:
            print("\n\n[!] Program ditutup.")
            sys.exit(0)

    # 2. MENU INPUT PILIHAN MODE TAHUN (Dengan Validasi Ketat)
    mode_spesifik = None
    try:
        print("\nPilih Mode Konversi Tahun:")
        print(" [1] Konversi Lengkap (Semua tahun dipisahkan otomatis)")
        print(" [2] Konversi Tahun Tertentu Saja (Misal: 2025)")

        # Looping akan terus berjalan sampai input valid (1 atau 2)
        while True:
            pilihan_mode = input("Masukkan pilihan (1/2): ").strip()

            if pilihan_mode == "1":
                print("-> Mode Aktif: Konversi Lengkap seluruh tahun.\n")
                break
            elif pilihan_mode == "2":
                while True:
                    mode_spesifik = input("Masukkan tahun yang ingin dikonversi (contoh: 2025): ").strip()
                    if mode_spesifik.isdigit() and len(mode_spesifik) == 4:
                        break
                    print("❌ Error: Format tahun harus berupa 4 digit angka (Contoh: 2025).")
                print(f"-> Mode Aktif: Hanya memproses data pada tahun {mode_spesifik}.\n")
                break
            else:
                print("❌ Pilihan tidak valid! Harap masukkan angka 1 atau 2 saja.")

    except KeyboardInterrupt:
        print("\n\n[!] Program ditutup.")
        sys.exit(0)

    # 3. Input nama awalan berkas
    try:
        base_prefix = input("Masukkan awalan nama file GeoJSON hasil (default: output): ").strip()
        if not base_prefix: base_prefix = "output"
        if base_prefix.endswith(".geojson"): base_prefix = base_prefix[:-8]
    except KeyboardInterrupt:
        print("\n\n[!] Program ditutup.")
        sys.exit(0)

    # Dictionary untuk memisahkan data berdasarkan tahun -> {"2023": [...], "2025": [...]}
    data_per_tahun = {}

    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        segments = source_data.get("semanticSegments", []) if isinstance(source_data, dict) else source_data

        print("\n⏳ Memproses koordinat... (Tekan Ctrl+C kapan saja untuk stop & simpan seadanya)")

        for segment in segments:
            if not segment or not isinstance(segment, dict): continue
            start_time, end_time = segment.get("startTime"), segment.get("endTime")
            
            # Mendeteksi tahun berdasarkan data string startTime (4 digit pertama)
            if start_time and len(start_time) >= 4:
                tahun = start_time[:4]
            else:
                tahun = "Tidak_Diketahui"

            # FILTER TAHUN: Abaikan data jika user memilih mode tahun tertentu dan tipenya tidak cocok
            if mode_spesifik and tahun != mode_spesifik:
                continue

            # Buat wadah list di dalam dictionary jika tahun baru terdeteksi
            if tahun not in data_per_tahun:
                data_per_tahun[tahun] = []
            
            try:
                if "visit" in segment:
                    visit_data = segment["visit"]
                    top_candidate = visit_data.get("topCandidate", {})
                    coords = clean_and_parse_coordinates(top_candidate.get("placeLocation", {}).get("latLng"))
                    if coords:
                        lng, lat = coords
                        nama_alamat = get_place_name(lat, lng)
                        print(f"📍 [{tahun}] Alamat ketemu: {nama_alamat}")
                        data_per_tahun[tahun].append({
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
                        data_per_tahun[tahun].append({
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
                        data_per_tahun[tahun].append({
                            "type": "Feature",
                            "geometry": {"type": "LineString", "coordinates": line_coordinates},
                            "properties": {"name": "Jalur Detail", "Tipe": "Rute Jalan Detail", "Waktu Mulai": start_time, "Waktu Selesai": end_time}
                        })

            except KeyboardInterrupt:
                print("\n\n⚠️ Dihentikan paksa oleh user (Ctrl+C)!")
                break

        # Sesi Menyimpan File GeoJSON Berdasarkan Tahun Berhasil Terisi
        daftar_file_terbuat = []
        print("\n⏳ Menyimpan data ke berkas tahunan...")
        
        for tahun, daftar_features in data_per_tahun.items():
            if not daftar_features:
                continue
                
            file_output_tahunan = f"{base_prefix}_{tahun}.geojson"
            with open(file_output_tahunan, 'w', encoding='utf-8') as f:
                json.dump({"type": "FeatureCollection", "features": daftar_features}, f, indent=2, ensure_ascii=False)
            
            print(f" -> Berhasil mengamankan {len(daftar_features)} data ke '{file_output_tahunan}'")
            daftar_file_terbuat.append(file_output_tahunan)

        # Memicu tawaran KML otomatis jika ada file yang sukses terbuat
        if daftar_file_terbuat:
            tawarkan_konversi_kml(daftar_file_terbuat)
        else:
            print("\n❌ Tidak ada data yang berhasil diproses sesuai kriteria pilihan Anda.")

    except Exception as e:
        print(f"Terjadi kesalahan: {str(e)}")

if __name__ == "__main__":
    main()
