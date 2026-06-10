# Google Location History (Semantic JSON) to GeoJSON & KML Multi-Converter

This repository provides a set of Python-based automation tools to extract, filter, and visualize **Semantic JSON** data (exported from Google Maps Timeline / Google Location History) into industry-standard spatial formats like **GeoJSON** and **KML**. It features automatic address translation (*Reverse Geocoding*) and an interactive dual-dashboard mapping system.

## ✨ Key Features

- **Spatial Double-Converter**: Converts raw Google Location History JSON into a unified GeoJSON file and automatically prompts for an instant KML (`.kml`) export for Google Earth.
- **Smart Year-Based Filtering**:
  - *Full Mode*: Processes all location segments and automatically splits them into individual yearly files (`_2023.geojson`, `_2024.geojson`, etc.).
  - *Specific Mode*: Targets and isolates data for a single chosen year (e.g., `2025`) to significantly minimize processing time.
- **Auto Reverse-Geocoding**: Translates raw coordinate pairs (`lat, lng`) into human-readable street names, villages, and cities using the free OpenStreetMap (Nominatim) API.
- **Graceful Interrupt Handler (Ctrl+C)**: If the processing loop is manually stopped, the script intercepts the break, instantly packages all successfully processed features, and closes the spatial file format properly to avoid data corruption.
- **Strict Terminal Validation**: Features foolproof user-input protection menus in the terminal.
- **Isolated Visualizer Dashboard (`visualizer.py`)**:
  - Converts GeoJSON paths into a standalone interactive map (`peta_rute_*.html`) powered by Plotly's latest `go.Scattermap` engine.
  - Draws explicit chronological journey lines tracing routes from point A to point B.
  - Equipped with standard on-map Zoom In/Out control buttons and view reset triggers.
  - Generates a completely separate HTML data table (`tabel_kronologis_*.html`) sorted from **newest to oldest** with automated long-address truncating to eliminate text overlapping.

---

## 🛠️ System Requirements & Installation

Ensure you have **Python 3.10+** installed on your system. Install the required external packages via your terminal using the following command:

```bash
python3 -m pip install pandas plotly geopy openpyxl
```

---

## 🚀 How to Use

Place your downloaded **Semantic JSON** file (from Google Takeout) inside the same folder directory as these scripts.

### 1. Converting Raw JSON to GeoJSON & KML
Execute the primary converter utility:
```bash
python3 json2geojson.py
```
**Interactive Workflow:**
1. Enter your source JSON file name.
2. Select the Year Conversion Mode (`1` for all years, `2` for a specific year query).
3. Set your custom output prefix name (Default: `output`).
4. Press `Ctrl+C` at any point to stop fetching live web addresses and safely store the current snapshot.
5. At the end of the script execution, type `y` to instantly generate a matching `.kml` file.

*Note: You can also manually invoke standalone GeoJSON to KML conversions at any time:*
```bash
python3 geojson2kml.py
```

### 2. Generating Interactive Maps & Data Tables
Once your GeoJSON file is generated, launch the layout visualizer:
```bash
python3 visualizer.py
```
**Interactive Workflow:**
1. The script automatically scans the working directory and lists all available GeoJSON files. Type the corresponding index number of the file you want to map.
2. Your default web browser will instantly fire open two separate tabs:
   - **`peta_rute_*.html`**: A full-canvas route map built over block-free *CartoDB Positron* layers.
   - **`tabel_kronologis_*.html`**: A clean, readable timeline log ordered from your most recent trips down to the oldest.

---

## 📂 Sample Directory Output Structure

After executing the workflows, your repository directory will be cleanly archived as follows:
```text
├── raw_json.json         # Raw source data from Google Takeout
├── json2geojson.py       # Main year-splitter and coordinate compiler
├── geojson2kml.py        # Independent GeoJSON-to-KML engine
├── visualizer.py         # Tab-isolated map and matrix generator
│
├── output_2025.geojson   # Extracted spatial GeoJSON segment
├── output_2025.kml       # Generated KML segment (Google Earth ready)
├── peta_rute_output_2025.html        # Interactive Path Visual Map
└── tabel_kronologis_output_2025.html # Newest-to-Oldest Data Table Layout
```

---

## 📝 Important API Usage Policy Notice
This script queries the public **OpenStreetMap Nominatim** search engine server, which strictly enforces a fair-use rate limit (maximum 1 request per second). To remain compliant, a `time.sleep(1)` lag is implemented within the address-fetching loop. If your location history dataset contains thousands of timeline footprints, conversion tasks will scale up in duration. We highly recommend utilizing the **Specific Year Mode** filter or the **Ctrl+C** graceful halt mechanism to easily control your queue times.
