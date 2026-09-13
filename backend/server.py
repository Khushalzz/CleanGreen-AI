"""
Clean and Green Tech — Backend & Static Application Server
Provides:
- Static file serving for the front end (index.html, admin.html, style.css, app.js, admin.js)
- GET /admin: Serves admin.html
- GET /api/osm/bins: Returns OpenStreetMap bins in Pune
- GET /api/complaints: Returns all complaints with enriched stats and URLs
- POST /api/submit-complaint: Receives waste image & GPS, runs agy garbage-vision headlessly,
  saves annotated photo, report.json, report.csv in unique GPS-timestamped complaint folder
- GET /complaints/<folder>/<filename>: Serves complaint assets (annotated images, reports)
"""

import http.server
import socketserver
import os
import sys
import json
import base64
import urllib.parse
import webbrowser
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "front end"
COMPLAINTS_DIR = BASE_DIR / "complaints"
COMPLAINTS_DIR.mkdir(parents=True, exist_ok=True)
OSM_BINS_FILE = BASE_DIR / "pune_osm_bins.json"

sys.path.insert(0, str(BACKEND_DIR))
from analyzer import save_initial_complaint, run_background_ai_analysis

PORT = 8000


class CleanGreenRequestHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path

        # 1. Admin redirect
        if path in ("/admin", "/admin/"):
            admin_file = FRONTEND_DIR / "admin.html"
            if admin_file.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(admin_file.stat().st_size))
                self.end_headers()
                with open(admin_file, "rb") as f:
                    self.copyfile(f, self.wfile)
                return

        # 2. API: OSM Waste Bins in Pune
        if path == "/api/osm/bins":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            bins_data = []
            if OSM_BINS_FILE.exists():
                try:
                    with open(OSM_BINS_FILE, "r", encoding="utf-8") as f:
                        bins_data = json.load(f)
                except Exception as e:
                    print("Error loading OSM bins file:", e)
            self.wfile.write(json.dumps({"bins": bins_data, "count": len(bins_data)}).encode('utf-8'))
            return

        # 3. API: List all complaints with enriched data
        if path == "/api/complaints":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            complaints = []
            if COMPLAINTS_DIR.exists():
                for folder in sorted(COMPLAINTS_DIR.iterdir(), reverse=True):
                    if folder.is_dir():
                        meta_file = folder / "metadata.json"
                        report_file = folder / "report.json"
                        ann_file = folder / "annotated_photo.jpg"
                        csv_file = folder / "report.csv"
                        
                        if meta_file.exists():
                            try:
                                with open(meta_file, "r", encoding="utf-8") as f:
                                    item = json.load(f)
                                
                                # Folder reference
                                item["folder_name"] = folder.name
                                item["folder_path"] = str(folder)
                                item["status"] = item.get("status", "Pending")

                                # Relative URLs
                                item["urls"] = {
                                    "original_image": f"/complaints/{folder.name}/{item.get('image_file', 'waste_photo.jpg')}",
                                    "annotated_image": f"/complaints/{folder.name}/annotated_photo.jpg" if ann_file.exists() else None,
                                    "json_report": f"/complaints/{folder.name}/report.json" if report_file.exists() else None,
                                    "csv_report": f"/complaints/{folder.name}/report.csv" if csv_file.exists() else None
                                }

                                if report_file.exists():
                                    item["analysis_status"] = "completed"
                                    try:
                                        with open(report_file, "r", encoding="utf-8") as rf:
                                            report_content = json.load(rf)
                                            items = report_content.get("items", [])
                                            item["stats"] = {
                                                "item_count": len(items),
                                                "sup_violations": sum(1 for it in items if it.get("sup_violation") is True),
                                                "hazard_flag": report_content.get("hazard_flag", False),
                                                "segregation_verdict": report_content.get("segregation_verdict", "unsegregated")
                                            }
                                            item["report"] = report_content
                                    except Exception:
                                        pass
                                else:
                                    item["analysis_status"] = "in_progress"
                                    item["stats"] = {
                                        "item_count": 0,
                                        "sup_violations": 0,
                                        "hazard_flag": False,
                                        "segregation_verdict": "Analyzing..."
                                    }

                                complaints.append(item)
                            except Exception as err:
                                print(f"Error reading complaint folder {folder.name}: {err}")
            
            self.wfile.write(json.dumps({"complaints": complaints, "total": len(complaints)}).encode('utf-8'))
            return

        # 4. Serve files from complaints/ directory
        if path.startswith("/complaints/"):
            rel_path = path[len("/complaints/"):]
            target_file = COMPLAINTS_DIR / rel_path
            try:
                target_file = target_file.resolve()
                if str(target_file).startswith(str(COMPLAINTS_DIR.resolve())) and target_file.is_file():
                    self.send_response(200)
                    mime_type = self.guess_type(str(target_file))
                    self.send_header('Content-Type', mime_type or 'application/octet-stream')
                    self.send_header('Content-Length', str(target_file.stat().st_size))
                    self.end_headers()
                    with open(target_file, "rb") as f:
                        self.copyfile(f, self.wfile)
                    return
            except Exception as e:
                print(f"Error serving complaint file: {e}")

            self.send_error(404, "Complaint file not found")
            return

        # Default static file serving from front end directory
        super().do_GET()

    def do_POST(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path

        # 1. Update Complaint Status
        if path.startswith("/api/complaints/") and path.endswith("/status"):
            content_length = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_length)
            try:
                data = json.loads(post_body.decode('utf-8'))
                new_status = data.get("status", "Pending")
                # path format: /api/complaints/<complaint_id>/status
                parts = path.strip("/").split("/")
                complaint_id = parts[2]

                # Find folder
                updated = False
                for folder in COMPLAINTS_DIR.iterdir():
                    if folder.is_dir():
                        meta_file = folder / "metadata.json"
                        if meta_file.exists():
                            with open(meta_file, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            if meta.get("complaint_id") == complaint_id:
                                meta["status"] = new_status
                                with open(meta_file, "w", encoding="utf-8") as f:
                                    json.dump(meta, f, indent=2)
                                updated = True
                                break

                self.send_response(200 if updated else 404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": updated, "status": new_status}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return

        # 1.5. Retry AI Analysis on Complaint
        if path.startswith("/api/complaints/") and path.endswith("/retry"):
            parts = path.strip("/").split("/")
            complaint_id = parts[2]
            target_folder = None
            target_img = None
            
            for folder in COMPLAINTS_DIR.iterdir():
                if folder.is_dir():
                    meta_file = folder / "metadata.json"
                    if meta_file.exists():
                        try:
                            with open(meta_file, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            if meta.get("complaint_id") == complaint_id:
                                target_folder = folder
                                target_img = folder / meta.get("image_file", "waste_photo.jpg")
                                meta["analysis_status"] = "in_progress"
                                if "analysis_error" in meta:
                                    del meta["analysis_error"]
                                with open(meta_file, "w", encoding="utf-8") as f:
                                    json.dump(meta, f, indent=2)
                                break
                        except Exception:
                            pass

            if target_folder and target_img and target_img.exists():
                threading.Thread(
                    target=run_background_ai_analysis,
                    args=(target_folder, target_img),
                    daemon=True
                ).start()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "complaint_id": complaint_id,
                    "message": "AI analysis retry started in background."
                }).encode('utf-8'))
                return
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Complaint not found or image missing"}).encode('utf-8'))
                return

        # 2. Submit Complaint
        if path == "/api/submit-complaint":
            content_length = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_length)

            try:
                content_type = self.headers.get('Content-Type', '')

                if 'application/json' in content_type:
                    data = json.loads(post_body.decode('utf-8'))
                    image_base64 = data.get('image_base64', '')
                    if ',' in image_base64:
                        image_base64 = image_base64.split(',', 1)[1]
                    image_bytes = base64.b64decode(image_base64)
                    filename = data.get('filename', 'waste_photo.jpg')
                    lat = float(data.get('latitude', 18.5178))
                    lng = float(data.get('longitude', 73.8151))
                    address = data.get('address', 'MIT-WPU Kothrud, Pune')
                    notes = data.get('notes', '')
                else:
                    self.send_error(400, "Content-Type must be application/json")
                    return

                # 1. Instantly save complaint folder and photo in < 50ms!
                folder_path, complaint_id, image_file_path = save_initial_complaint(
                    base_dir=COMPLAINTS_DIR,
                    image_bytes=image_bytes,
                    image_filename=filename,
                    lat=lat,
                    lng=lng,
                    address=address,
                    notes=notes
                )

                print(f"[BACKEND] Complaint {complaint_id} saved instantly in {folder_path.name}!")

                # 2. Spawn headless Vision AI analysis in a background daemon thread
                ai_thread = threading.Thread(
                    target=run_background_ai_analysis,
                    args=(folder_path, image_file_path),
                    daemon=True
                )
                ai_thread.start()

                # 3. Immediately return response to citizen (< 100ms response time!)
                resp_payload = {
                    "status": "success",
                    "complaint_id": complaint_id,
                    "folder_name": folder_path.name,
                    "address": address,
                    "coordinates": {"latitude": lat, "longitude": lng},
                    "message": "Complaint registered successfully! Sanitation operations dispatched."
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(resp_payload, indent=2).encode('utf-8'))
                return

            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                return

        self.send_error(404, "Endpoint not found")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def run():
    server_address = ('', PORT)
    httpd = ThreadedHTTPServer(server_address, CleanGreenRequestHandler)
    url = f"http://localhost:{PORT}"
    print("=" * 70)
    print(" CLEAN AND GREEN TECH — BACKEND & VISION AI SERVER")
    print(f" Citizen Web App:          {url}")
    print(f" Admin Dashboard:          {url}/admin")
    print(f" OSM Bins Tracked (Pune):  {OSM_BINS_FILE}")
    print(f" Complaints Directory:     {COMPLAINTS_DIR}")
    print("=" * 70)

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
        httpd.shutdown()


if __name__ == "__main__":
    run()
