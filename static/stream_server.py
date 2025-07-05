#!/usr/bin/env python3
# stream_server.py (version corrigée)

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from picamera2 import Picamera2
import io
import threading
import time
from PIL import Image
import os
from datetime import datetime

PORT = 8080

class StreamingOutput:
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def set_frame(self, frame):
        with self.condition:
            self.frame = frame
            self.condition.notify_all()

class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Main HTML page
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>PiBirdHouse Stream</title>
  <link rel="icon" type="image/png" href="/static/logo.png">
  <style>
    body { margin:0; background:#f4f4f4; font-family:sans-serif; text-align:center; }
    h1 { background:#1b8335; color:white; padding:10px; }
    img { width:90%; max-width:640px; }
    button {
      background:#1b8335; color:white; border:none; padding:10px 20px;
      font-size:1em; border-radius:5px; cursor:pointer; margin:10px;
    }
    button:hover { background:#14682a; }
  </style>
</head>
<body>
  <h1>PiBirdHouse Live Stream</h1>
  <img src="/stream.mjpg">
  <br>
  <button onclick="capture()">Capture Image</button>
  <script>
    function capture() {
      fetch('/capture').then(res => {
        if(res.ok) alert('✅ Image captured!');
        else alert('❌ Capture failed.');
      });
    }
  </script>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(frame)))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                print(f"📷 Client disconnected: {e}")
        elif self.path == '/capture':
            # Save current frame to Images folder
            script_dir = os.path.dirname(os.path.abspath(__file__))
            images_dir = os.path.join(script_dir, '../Images')
            os.makedirs(images_dir, exist_ok=True)
            filename = datetime.now().strftime("%Y%m%d_%H%M%S.jpg")
            path = os.path.join(images_dir, filename)
            with output.condition:
                if output.frame:
                    with open(path, 'wb') as f:
                        f.write(output.frame)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"OK")
                    print(f"📸 Image captured: {filename}")
                else:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b"No frame")
        elif self.path == '/static/logo.png':
            # Serve logo from static folder
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(script_dir, 'logo.png')
            if not os.path.isfile(logo_path):
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            with open(logo_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)
            self.end_headers()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

if __name__ == '__main__':
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    output = StreamingOutput()

    # Start camera
    picam2.start()

    def capture_frames():
        while True:
            frame = picam2.capture_array()
            img = Image.fromarray(frame).convert('RGB')
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            output.set_frame(buf.getvalue())
            time.sleep(0.1)  # ~10 fps

    t = threading.Thread(target=capture_frames, daemon=True)
    t.start()

    try:
        server = ThreadedHTTPServer(('', PORT), StreamingHandler)
        print(f"✅ Stream server running at http://0.0.0.0:{PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down stream server.")
    finally:
        picam2.stop()
        server.server_close()
