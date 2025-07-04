import io
import time
import threading
import http.server
import socketserver
import os
from picamera2 import Picamera2
from PIL import Image

# Initialisation de la caméra
picam2 = Picamera2()
picam2.start()

# Répertoire de sauvegarde des images
save_dir = "/home/USER_NAME/PiBirdHouse/Images"
os.makedirs(save_dir, exist_ok=True)

# Variable pour stocker la dernière image
latest_frame = None
lock = threading.Lock()

def capture_frames():
    global latest_frame
    while True:
        frame = picam2.capture_array()
        image = Image.fromarray(frame).convert("RGB")
        with io.BytesIO() as buf:
            image.save(buf, format='JPEG')
            with lock:
                latest_frame = buf.getvalue()
        time.sleep(0.1)  # ≈ 10 FPS

class MJPEGHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>PiBirdHouse v1.0 - Flux Vidéo</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin: 0; padding: 20px; background-color: #f4f4f4; }
        header { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 20px; }
        header img { height: 50px; }
        h1 { margin: 0; font-size: 24px; color: #333; }
        .video-container { background: #fff; padding: 10px; border-radius: 8px; display: inline-block; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        button { padding: 10px 20px; font-size: 16px; margin-top: 10px; background-color: #1b8335; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #45a049; }
        footer { margin-top: 20px; color: #888; font-size: 14px; }
    </style>
</head>
<body>
    <header>
        <h1>PiBirdHouse v1.0 - Flux Vidéo</h1>
    </header>

    <div class="video-container">
        <img src="/video" style="max-width:100%; border:1px solid #aaa;">
        <form method="POST" action="/capture">
            <button type="submit">📸 Capturer l'image</button>
        </form>
    </div>

    <footer>
        An Aerodynamics Project
    </footer>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))

        elif self.path == '/video':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            while True:
                with lock:
                    frame = latest_frame
                if frame:
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n\r\n")
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
                time.sleep(0.1)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/capture':
            with lock:
                frame = latest_frame
            if frame:
                filename = time.strftime("capture_%Y%m%d_%H%M%S.jpg")
                filepath = os.path.join(save_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(frame)
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

# Lancement du thread de capture d'images
threading.Thread(target=capture_frames, daemon=True).start()

# Serveur HTTP
PORT = 8080
with socketserver.TCPServer(("", PORT), MJPEGHandler) as httpd:
    print(f"Serveur MJPEG en cours sur http://0.0.0.0:{PORT}")
    httpd.serve_forever()
