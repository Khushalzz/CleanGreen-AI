# CleanSpot - Waste Reporting & GPS Pinpoint Frontend

A lightweight, modern web frontend allowing citizens and municipal auditors to upload waste photos and pinpoint exact geographical coordinates on an interactive map (pre-configured to **MIT-WPU, Kothrud, Pune**).

---

## 🌟 Key Features

1. **Photo Upload with Live Preview**:
   - Drag-and-drop or file browser selection.
   - Image thumbnail preview with file metadata (size, filename).
   - EXIF GPS metadata auto-detection: if the uploaded photo contains geotags, a prompt allows instantly setting the pin to the photo's original location.

2. **Interactive GPS Map (Leaflet.js + OpenStreetMap)**:
   - **Default Coordinates**: `18.517800, 73.815100` (MIT-WPU, Paud Road, Kothrud, Pune).
   - **Draggable Marker**: Drag the pin anywhere to update coordinates.
   - **Click to Place**: Click anywhere on the map to relocate the marker.
   - **Live Reverse Geocoding**: Automatically resolves latitude/longitude to street address via OpenStreetMap Nominatim.
   - **Locate Me**: One-click device GPS locator button using browser Geolocation API.
   - **MIT-WPU Preset**: One-click button to reset the view and pin back to MIT-WPU Kothrud.

3. **Report Generation & JSON Export**:
   - Select waste category (Plastics, Organic, Overflowing Bin, Debris, etc.) and add notes.
   - Generates a structured waste report with image preview, coordinates, timestamp, and address.
   - Downloadable JSON report payload.

---

## 🚀 How to Run on Localhost

### Option 1: Double-click (Windows)
Double click `start.bat` in the `front end` folder. It will automatically detect Python or Node and launch your browser at `http://localhost:8000`.

### Option 2: Python (Recommended)
Open a terminal in the `front end` directory and run:
```bash
python server.py
# or
python -m http.server 8000
```
Then open `http://localhost:8000` in your web browser.

### Option 3: Node / NPX
```bash
npx serve . -l 8000
```

### Option 4: Direct Browser
You can also open `index.html` directly in Google Chrome, Microsoft Edge, or Firefox.
