import json
import os
import sys
import glob
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

def clean_address(full_address):
    if not full_address or "Coordinates" in full_address:
        return full_address
    parts = [p.strip() for p in full_address.split(',')]
    if len(parts) > 2:
        return ", ".join(parts[:2])
    return full_address

def parse_geojson(geojson_file):
    with open(geojson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = []
    features = data.get("features", [])

    for feature in features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        # Updated to check for "Type" instead of "Tipe"
        tipe = properties.get("Type", "")

        # Updated to check for "Place Visit" instead of "Kunjungan Tempat"
        if tipe == "Place Visit" and geometry.get("type") == "Point":
            coords = geometry.get("coordinates")
            if not coords or len(coords) < 2:
                continue

            lng = float(coords[0])
            lat = float(coords[1])

            nama_tempat_raw = properties.get("name") or "Unknown Place"
            nama_tempat = clean_address(nama_tempat_raw)

            # Updated property keys
            waktu_mulai_raw = properties.get("Start Time", "")
            waktu_selesai_raw = properties.get("End Time", "")

            if waktu_mulai_raw:
                try:
                    clean_time = waktu_mulai_raw.split(".")[0].split("+")[0]
                    dt = datetime.strptime(clean_time, "%Y-%m-%dT%H:%M:%S")

                    day_name = dt.strftime("%A")
                    tanggal = dt.strftime("%d-%m-%Y")
                    jam_mulai = dt.strftime("%H:%M")

                    jam_selesai = "-"
                    if waktu_selesai_raw:
                        clean_end = waktu_selesai_raw.split(".")[0].split("+")[0]
                        dt_end = datetime.strptime(clean_end, "%Y-%m-%dT%H:%M:%S")
                        jam_selesai = dt_end.strftime("%H:%M")

                    rows.append({
                        "Day": day_name,
                        "Date": tanggal,
                        "Place Name": nama_tempat,
                        "Time": f"{jam_mulai} to {jam_selesai}",
                        "Latitude": lat,
                        "Longitude": lng,
                        "_sort_date": dt
                    })
                except Exception:
                    continue

    df = pd.DataFrame(rows)
    if not df.empty:
        # Sort from newest to oldest
        df = df.sort_values(by="_sort_date", ascending=False).reset_index(drop=True)
    return df

def create_separate_map(df, suffix_name):
    """Creates an HTML file specifically for the route map using the latest Scattermap module"""
    fig_map = go.Figure()

    # Reverse temporarily for chronological rendering of route lines
    df_chronological = df.iloc[::-1]

    # 1. Add connecting route lines (Using go.Scattermap)
    for i in range(len(df_chronological) - 1):
        origin = df_chronological.iloc[i]
        destination = df_chronological.iloc[i+1]
        fig_map.add_trace(go.Scattermap(
            mode="markers+lines",
            lon=[origin["Longitude"], destination["Longitude"]],
            lat=[origin["Latitude"], destination["Latitude"]],
            marker=dict(size=0),
            line=dict(width=3, color="#e74c3c"),
            hoverinfo="skip"
        ))

    # 2. Add location pin markers (Using go.Scattermap)
    fig_map.add_trace(go.Scattermap(
        lat=df["Latitude"],
        lon=df["Longitude"],
        mode="markers",
        marker=dict(size=12, color="#2ce7ad", opacity=0.9),
        hovertemplate="<b>%{text}</b><br>Visit Time: %{customdata}<br><extra></extra>",
        text=df["Place Name"],
        customdata=df["Time"]
    ))

    center_lat = float(df["Latitude"].mean())
    center_lng = float(df["Longitude"].mean())

    fig_map.update_layout(
        title=f"🗺️ Journey Path Map - {suffix_name}",
        title_font=dict(size=16, family="Arial Black"),
        showlegend=False,
        map=dict(
            style="carto-positron",
            center=dict(lat=center_lat, lon=center_lng),
            zoom=12
        ),
        margin=dict(l=15, r=15, t=60, b=15),
        height=650
    )

    output_map = f"route_map_{suffix_name}.html"
    config_options = {
        'modeBarButtonsToAdd': ['zoomInMap', 'zoomOutMap', 'resetViewMap'],
        'displayModeBar': True
    }
    fig_map.write_html(output_map, config=config_options)
    print(f"👉 MAP file saved at: '{output_map}'")
    return output_map

def create_separate_table(df, suffix_name):
    """Creates an HTML file specifically for the table chart"""
    fig_table = go.Figure(data=[go.Table(
        header=dict(
            values=["Day", "Date", "Place Name", "Visit Time"],
            fill_color='#2c3e50', align='left',
            font=dict(color='white', size=13, family="Arial Black"), height=35
        ),
        cells=dict(
            values=[df["Day"], df["Date"], df["Place Name"], df["Time"]],
            fill_color='#fcfcfc', align='left',
            font=dict(color='#333333', size=12, family="Arial"), height=30
        )
    )])

    fig_table.update_layout(
        title=f"📊 Place Visit History Table (Newest -> Oldest) - {suffix_name}",
        title_font=dict(size=16, family="Arial Black"),
        margin=dict(l=15, r=15, t=60, b=15),
        height=600
    )

    output_table = f"chronological_table_{suffix_name}.html"
    fig_table.write_html(output_table)
    print(f"👉 TABLE file saved at: '{output_table}'")
    return output_table

def main():
    print("=== GeoJSON to Separate Map & Table Converter (Yearly Compatible) ===")

    # Automatically detect any .geojson files in the current folder
    files_found = glob.glob("*.geojson")

    if files_found:
        print("\nGeoJSON files found in the current folder:")
        for idx, file in enumerate(files_found, 1):
            print(f" [{idx}] {file}")
        print(" [0] Enter filename manually")

        choice = input("\nSelect file number to process (default: 1): ").strip()
        if not choice:
            input_file = files_found[0]
        elif choice == "0":
            input_file = input("Enter manual GeoJSON filename: ").strip()
        else:
            try:
                input_file = files_found[int(choice) - 1]
            except (ValueError, IndexError):
                print("❌ Invalid choice, using the first file.")
                input_file = files_found[0]
    else:
        input_file = input("Enter GeoJSON filename (default: output.geojson): ").strip()
        if not input_file:
            input_file = "output.geojson"

    if not os.path.exists(input_file):
        print(f"❌ Error: File '{input_file}' not found.")
        sys.exit(1)

    # Get filename without extension for HTML output naming
    suffix_name = os.path.splitext(os.path.basename(input_file))[0]

    print(f"⏳ Splitting map and table processing for '{input_file}'...")
    df = parse_geojson(input_file)

    if df.empty:
        print("❌ No valid place visit data to process.")
        return

    file_peta = create_separate_map(df, suffix_name)
    file_tabel = create_separate_table(df, suffix_name)

    print("\n Conversion Successful! Opening results in your browser...")
    import webbrowser
    webbrowser.open('file://' + os.path.realpath(file_peta))
    webbrowser.open('file://' + os.path.realpath(file_tabel))

if __name__ == "__main__":
    main()
