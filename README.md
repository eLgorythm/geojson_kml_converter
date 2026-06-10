# Google Location History (Semantic JSON) to GeoJSON & KML Multi-Converter

Repositori ini berisi seperangkat alat otomasi berbasis Python untuk mengekstrak, menyaring, dan memvisualisasikan data **Semantic JSON** (format data dari Google Maps Timeline / Google Location History) menjadi file spasial standar industri **GeoJSON** dan **KML**, lengkap dengan fitur otomatis terjemahan nama alamat (*Reverse Geocoding*) dan dasbor peta interaktif.

## ✨ Fitur Utama

- **Double-Converter Spasial**: Mengonversi JSON riwayat lokasi dari Google ke format GeoJSON tunggal dan secara otomatis menawarkan ekspor instan ke berkas KML (`.kml`) untuk Google Earth.
- **Penyaringan Pintar Berbasis Tahun**: 
  - *Mode Lengkap*: Memproses semua data spasial dan memisahnya otomatis per file tahun (`_2023.geojson`, `_2024.geojson`, dll).
  - *Mode Spesifik*: Hanya menyaring dan memproses data pada tahun tertentu (misal: `2025`) guna memangkas durasi pemrosesan.
- **Auto Reverse-Geocoding**: Mengubah data koordinat mentah (`lat, lng`) menjadi alamat jalan, desa, dan kota asli menggunakan API gratis dari OpenStreetMap (Nominatim).
- **Graceful Interrupt Handler (Ctrl+C)**: Jika proses dihentikan paksa di tengah jalan, script akan mengamankan dan menutup struktur file spasial seadanya agar data yang terproses tidak rusak/korup.
- **Validasi Terminal yang Ketat**: Dilengkapi dengan pencegahan salah input di menu terminal.
- **Dasbor Visualisasi Terpisah (`visualizer.py`)**: 
  - Mengonversi GeoJSON menjadi peta rute jalan interaktif (`peta_rute_*.html`) menggunakan teknologi `go.Scattermap` terbaru dari Plotly.
  - Menarik garis kronologis perjalanan penghubung dari titik A ke titik B.
  - Dilengkapi tombol navigasi Zoom In/Out manual dan reset view.
  - Membuat tabel HTML terpisah (`tabel_kronologis_*.html`) dengan urutan data **terbaru ke terlama** dan pembersihan teks alamat panjang agar tidak tumpang tindih.

---

## 🛠️ Kebutuhan Sistem & Instalasi

Pastikan komputer Anda sudah terpasang **Python 3.10+**. Instal library eksternal yang dibutuhkan melalui terminal dengan perintah berikut:

```bash
python3 -m pip install pandas plotly geopy openpyxl
```

---

## 🚀 Cara Penggunaan

Pastikan file **Semantic JSON** hasil unduhan dari Google Takeout Anda diletakkan di dalam folder yang sama dengan script ini.

### 1. Mengonversi JSON Mentah ke GeoJSON & KML
Jalankan script converter utama:
```bash
python3 json2geojson.py
```
**Alur Interaksi:**
1. Masukkan nama file JSON sumber Anda.
2. Pilih Mode Konversi Tahun (`1` untuk semua tahun, `2` untuk tahun spesifik saja).
3. Tentukan awalan nama file output (Default: `output`).
4. Tekan `Ctrl+C` kapan saja jika ingin menyudahi pencarian alamat internet dan menyimpan hasil sementara.
5. Di akhir proses, ketik `y` jika ingin langsung melahirkan file kembar berformat `.kml`.
6. Kamu bisa konversi geojson ke kml, secara terpisah.
```bash
python3 geojson2kml.py
```
### 2. Membuat Grafik Peta Rute & Tabel Interaktif
Setelah file GeoJSON terbentuk, jalankan script visualisasi:
```bash
python3 visualizer.py
```
**Alur Interaksi:**
1. Script akan otomatis memindai folder dan menampilkan daftar file GeoJSON yang tersedia. Pilih nomor urut berkas yang ingin digambar.
2. Browser internet Anda akan otomatis membuka 2 tab baru:
   - **`peta_rute_*.html`**: Peta rute berbasis *CartoDB Positron* (bebas pemblokiran).
   - **`tabel_kronologis_*.html`**: Tabel riwayat perjalanan rapi dari waktu terbaru ke terlama.

---

## 📂 Contoh Struktur Output Berkas

Setelah seluruh script dijalankan, manajemen folder Anda akan terarsip rapi seperti berikut:
```text
├── raw_json.json         # File sumber dari Google Maps
├── json2geojson.py   # Script converter utama
├── geojson2kml.py           # Script konversi KML terpisah
├── visualizer.py                   # Script visualisasi peta & tabel
│
├── output_2025.geojson     # Hasil GeoJSON per tahun
├── output_2025.kml         # Hasil KML per tahun (Google Earth)
├── peta_rute_output_2025.html     # Visual Peta Interaktif
└── tabel_kronologis_output_2025.html # Visual Tabel Terbaru->Terlama
```

---

## 📝 Catatan Penting Penggunaan API Alamat
Script ini menggunakan server pencarian **OpenStreetMap Nominatim** gratis yang menerapkan kebijakan pembatasan akses ketat (1 request per detik). Oleh karena itu, dipasang fungsi `time.sleep(1)` pada script utama. Jika dataset riwayat lokasi Anda memiliki ribuan titik kunjungan, proses konversi akan memakan waktu. Gunakan fitur **Mode Spesifik Tahun** atau interupsi **Ctrl+C** untuk membatasi waktu tunggu sesuai kebutuhan Anda.
