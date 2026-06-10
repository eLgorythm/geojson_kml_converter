import os
import sys
import subprocess

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu():
    while True:
        clear_screen()
        print("================================================")
        print("   GOOGLE LOCATION HISTORY TOOLKIT (MASTER)     ")
        print("================================================")
        print(" [1] Convert Semantic JSON to GeoJSON (Yearly)")
        print(" [2] Convert GeoJSON to KML (for Google Earth)")
        print(" [3] Visualize GeoJSON (Interactive Map & Table)")
        print(" [4] Install Missing Dependencies (ijson, geopy, etc.)")
        print(" [0] Exit")
        print("------------------------------------------------")
        
        choice = input("Select an option (0-4): ").strip()
        
        if choice == "1":
            subprocess.run([sys.executable, "json2geojson.py"])
            input("\nPress Enter to return to menu...")
        elif choice == "2":
            subprocess.run([sys.executable, "geojson2kml.py"])
            input("\nPress Enter to return to menu...")
        elif choice == "3":
            subprocess.run([sys.executable, "visualizer.py"])
            input("\nPress Enter to return to menu...")
        elif choice == "4":
            print("⏳ Installing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "geopy", "pandas", "plotly", "ijson"])
            input("\nInstallation complete. Press Enter to return to menu...")
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            input("Invalid choice. Press Enter to try again...")

if __name__ == "__main__":
    main_menu()
