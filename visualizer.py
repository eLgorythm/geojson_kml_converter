import json
import os
import sys
import glob
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

HARI_INDO = {
    'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
    'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
}

def bersihkan_alamat(alamat_full):
    if not alamat_full or "Koordinat" in alamat_full:
        return alamat_full
    parts = [p.strip() for p in alamat_full.split(',')]
    if len(parts) > 2:
        return ", ".join(parts[:2])
    return alamat_full

def parse_geojson(geojson_file):
    with open(geojson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = []
    features = data.get("features", [])

    for feature in features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        tipe = properties.get("Tipe", "")

        if tipe == "Kunjungan Tempat" and geometry.get("type") == "Point":
            coords = geometry.get("coordinates")
            if not coords or len(coords) < 2:
                continue

            lng = float(coords[0])
            lat = float(coords[1])

            nama_tempat_raw = properties.get("name") or "Tempat Tidak Diketahui"
            nama_tempat = bersihkan_alamat(nama_tempat_raw)

            waktu_mulai_raw = properties.get("Waktu Mulai", "")
            waktu_selesai_raw = properties.get("Waktu Selesai", "")

            if waktu_mulai_raw:
                try:
                    clean_time = waktu_mulai_raw.split(".")[0].split("+")[0]
                    dt = datetime.strptime(clean_time, "%Y-%m-%dT%H:%M:%S")

                    hari_indo = HARI_INDO.get(dt.strftime("%A"), dt.strftime("%A"))
                    tanggal = dt.strftime("%d-%m-%Y")
                    jam_mulai = dt.strftime("%H:%M")

                    jam_selesai = "-"
                    if waktu_selesai_raw:
                        clean_end = waktu_selesai_raw.split(".")[0].split("+")[0]
                        dt_end = datetime.strptime(clean_end, "%Y-%m-%dT%H:%M:%S")
                        jam_selesai = dt_end.strftime("%H:%M")

                    rows.append({
                        "Hari": hari_indo,
                        "Tanggal": tanggal,
                        "Nama Tempat": nama_tempat,
                        "Waktu": f"{jam_mulai} s/d {jam_selesai}",
                        "Latitude": lat,
                        "Longitude": lng,
                        "_sort_date": dt
                    })
                except Exception:
                    continue

    df = pd.DataFrame(rows)
    if not df.empty:
        # PERBAIKAN: Mengurutkan dari yang TERBARU ke TERLAMA (ascending=False)
        df = df.sort_values(by="_sort_date", ascending=False).reset_index(drop=True)
    return df

def buat_peta_terpisah(df, suffix_name):
    """Membuat file HTML khusus peta rute menggunakan modul Scattermap terbaru"""
    fig_map = go.Figure()

    # Agar penarikan garis rute A ke B tetap berjalan kronologis (dari masa lalu ke masa depan),
    # kita balik sementara urutan dataframe khusus untuk rendering garisnya saja.
    df_chronological = df.iloc[::-1]

    # 1. Tambahkan garis rute penghubung A ke B (Menggunakan go.Scattermap)
    for i in range(len(df_chronological) - 1):
        asal = df_chronological.iloc[i]
        tujuan = df_chronological.iloc[i+1]
        fig_map.add_trace(go.Scattermap(
            mode="markers+lines",
            lon=[asal["Longitude"], tujuan["Longitude"]],
            lat=[asal["Latitude"], tujuan["Latitude"]],
            marker=dict(size=0),
            line=dict(width=3, color="#e74c3c"),
            hoverinfo="skip"
        ))

    # 2. Tambahkan marker pin lokasi berhenti (Menggunakan go.Scattermap)
    fig_map.add_trace(go.Scattermap(
        lat=df["Latitude"],
        lon=df["Longitude"],
        mode="markers",
        marker=dict(size=12, color="#2ce7ad", opacity=0.9),
        hovertemplate="<b>%{text}</b><br>Waktu Kunjungan: %{customdata}<br><extra></extra>",
        text=df["Nama Tempat"],
        customdata=df["Waktu"]
    ))

    pusat_lat = float(df["Latitude"].mean())
    pusat_lng = float(df["Longitude"].mean())

    fig_map.update_layout(
        title=f"🗺️ Peta Jalur Penghubung Perjalanan - {suffix_name}",
        title_font=dict(size=16, family="Arial Black"),
        showlegend=False,
        map=dict(
            style="carto-positron",
            center=dict(lat=pusat_lat, lon=pusat_lng),
            zoom=12
        ),
        margin=dict(l=15, r=15, t=60, b=15),
        height=650
    )

    output_map = f"peta_rute_{suffix_name}.html"
    config_options = {
        'modeBarButtonsToAdd': ['zoomInMap', 'zoomOutMap', 'resetViewMap'],
        'displayModeBar': True
    }
    fig_map.write_html(output_map, config=config_options)
    print(f"👉 File PETA disimpan di  : '{output_map}'")
    return output_map

def buat_tabel_terpisah(df, suffix_name):
    """Membuat file HTML khusus grafik tabel"""
    fig_table = go.Figure(data=[go.Table(
        header=dict(
            values=["Hari", "Tanggal", "Nama Tempat", "Waktu Kunjungan"],
            fill_color='#2c3e50', align='left',
            font=dict(color='white', size=13, family="Arial Black"), height=35
        ),
        cells=dict(
            values=[df["Hari"], df["Tanggal"], df["Nama Tempat"], df["Waktu"]],
            fill_color='#fcfcfc', align='left',
            font=dict(color='#333333', size=12, family="Arial"), height=30
        )
    )])

    fig_table.update_layout(
        title=f"📊 Grafik Tabel Riwayat Kunjungan Tempat (Terbaru -> Terlama) - {suffix_name}",
        title_font=dict(size=16, family="Arial Black"),
        margin=dict(l=15, r=15, t=60, b=15),
        height=600
    )

    output_table = f"tabel_kronologis_{suffix_name}.html"
    fig_table.write_html(output_table)
    print(f"👉 File TABEL disimpan di : '{output_table}'")
    return output_table

def main():
    print("=== GeoJSON to Separate Map & Table Converter (Yearly Compatible) ===")

    # Otomatis mendeteksi file .geojson apa saja yang ada di folder saat ini
    files_found = glob.glob("*.geojson")

    if files_found:
        print("\nBerkas GeoJSON yang ditemukan di folder saat ini:")
        for idx, file in enumerate(files_found, 1):
            print(f" [{idx}] {file}")
        print(" [0] Masukkan nama file manual secara kustom")

        pilihan = input("\nPilih nomor file yang ingin diproses (default: 1): ").strip()
        if not pilihan:
            input_file = files_found[0]
        elif pilihan == "0":
            input_file = input("Masukkan nama file GeoJSON manual: ").strip()
        else:
            try:
                input_file = files_found[int(pilihan) - 1]
            except (ValueError, IndexError):
                print("❌ Pilihan tidak valid, menggunakan file pertama.")
                input_file = files_found[0]
    else:
        input_file = input("Masukkan nama file GeoJSON (default: output.geojson): ").strip()
        if not input_file:
            input_file = "output.geojson"

    if not os.path.exists(input_file):
        print(f"❌ Error: File '{input_file}' tidak ditemukan.")
        sys.exit(1)

    # Ambil nama file tanpa ekstensi untuk dijadikan pengenal output HTML (misal: output_2025)
    suffix_name = os.path.splitext(os.path.basename(input_file))[0]

    print(f"⏳ Memisahkan pengolahan grafik peta dan tabel harian untuk '{input_file}'...")
    df = parse_geojson(input_file)

    if df.empty:
        print("❌ Tidak ada data kunjungan tempat yang valid untuk diproses.")
        return

    file_peta = buat_peta_terpisah(df, suffix_name)
    file_tabel = buat_tabel_terpisah(df, suffix_name)

    print("\n Konversi Berhasil! Membuka file hasil di browser Anda...")
    import webbrowser
    webbrowser.open('file://' + os.path.realpath(file_peta))
    webbrowser.open('file://' + os.path.realpath(file_tabel))

if __name__ == "__main__":
    main()
