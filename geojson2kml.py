import json
import os
import sys
import glob
import xml.etree.ElementTree as ET
from xml.dom import minidom

def convert_geojson_to_kml(geojson_data, base_name):
    kml = ET.Element("kml", xmlns="http://opengis.net")
    document = ET.SubElement(kml, "Document")
    
    doc_name = ET.SubElement(document, "name")
    doc_name.text = f"KML - {base_name}"
    
    features = geojson_data.get("features", [])
    for feature in features:
        geometry = feature.get("geometry")
        properties = feature.get("properties", {})
        
        if not geometry:
            continue
            
        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates")
        # Supports both English "Type" and Indonesian "Tipe" labels
        placemark_name = properties.get("name") or properties.get("Type") or properties.get("Tipe") or f"Object {geom_type}"
        
        desc_parts = [f"<b>{k}:</b> {v}" for k, v in properties.items()]
        placemark_desc = "<br>".join(desc_parts)

        if geom_type == "Point" and coordinates:
            placemark = ET.SubElement(document, "Placemark")
            ET.SubElement(placemark, "name").text = str(placemark_name)
            ET.SubElement(placemark, "description").text = placemark_desc
            
            point = ET.SubElement(placemark, "Point")
            coords_el = ET.SubElement(point, "coordinates")
            lng, lat = coordinates[:2]
            coords_el.text = f"{lng},{lat},0"

        elif geom_type == "LineString" and coordinates:
            placemark = ET.SubElement(document, "Placemark")
            ET.SubElement(placemark, "name").text = str(placemark_name)
            ET.SubElement(placemark, "description").text = placemark_desc
            
            linestring = ET.SubElement(placemark, "LineString")
            ET.SubElement(linestring, "tessellate").text = "1"
            
            coords_el = ET.SubElement(linestring, "coordinates")
            coord_strings = [f"{coord[0]},{coord[1]},0" for coord in coordinates]
            coords_el.text = " ".join(coord_strings)
            
    xml_string = ET.tostring(kml, encoding='utf-8')
    parsed_xml = minidom.parseString(xml_string)
    return parsed_xml.toprettyxml(indent="  ", encoding="utf-8")

def main(input_file=None):
    if not input_file:
        print("\n=== GeoJSON to KML Converter ===")
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
            input_file = input("Enter source GeoJSON filename (example: output.geojson): ").strip()
            if not input_file:
                input_file = "output.geojson"

    if not os.path.exists(input_file):
        print(f"❌ Error: File '{input_file}' not found.")
        return

    output_file = input_file.rsplit('.', 1)[0] + ".kml"
    base_name = os.path.basename(output_file).rsplit('.', 1)[0]

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
            
        print(f"⏳ Converting '{input_file}' to KML...")
        kml_bytes = convert_geojson_to_kml(geojson_data, base_name)
        with open(output_file, 'wb') as f:
            f.write(kml_bytes)
            
        print(f" -> [KML Success] KML file saved as: '{output_file}'")
    except Exception as e:
        print(f"❌ KML conversion failed: {str(e)}")

if __name__ == "__main__":
    # If called by another script, get the filename argument if available
    file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(file_arg)
