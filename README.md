# Google Semantic JSON to GeoJSON & KML Tools

A collection of Python scripts to process, convert, and visualize Google Maps Semantic Location History data (from Google Takeout). These tools allow you to split your history by year, convert results to KML for Google Earth, and generate interactive web-based maps and tables.

## 🚀 Features

*   **`main.py` (Orchestrator)**: The master script to access all tools from a single menu.
*   **`json2geojson.py`**: Converts Google Semantic JSON to GeoJSON.
    *   **Large File Support**: Uses `ijson` for streaming processing (low memory usage).
    *   Automatic yearly splitting or specific year filtering.
    *   Reverse geocoding using Nominatim.
    *   Integrated automation: Offers KML conversion and Visualization after processing.
*   **`geojson2kml.py`**: Converts GeoJSON files to KML format.
    *   Automatic file detection in the current directory.
*   **`visualizer.py`**: Generates interactive HTML visualizations (Route Map & Chronological Table).

## 📦 Prerequisites

Ensure you have Python 3.x installed. You can install all dependencies via `main.py` or manually:

```bash
pip install geopy pandas plotly ijson
```

## 🛠️ Usage

### 1. Preparation
Download your **Location History (Semantic Location History)** from [Google Takeout](https://takeout.google.com/) in JSON format.

### 2. Run the Master Script
The easiest way to use these tools is via the orchestrator:
```bash
python main.py
```

### 3. Manual Usage
You can still run individual scripts if preferred:
- `python json2geojson.py`: Full conversion flow.
- `python geojson2kml.py`: Manual KML conversion.
- `python visualizer.py`: Manual visualization generation.

## 📝 Configuration

- **Memory Efficiency**: The tools now prefer `ijson`. If `ijson` is not installed, it will fallback to standard `json` (which uses more RAM).
- **Rate Limiting**: `json2geojson.py` includes a 1-second delay for address lookups to comply with Nominatim's terms of service.

## 📄 License
This project is open-source and free to use.
