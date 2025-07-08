# PiBirdHouse: A Smart Birdhouse with Raspberry Pi and Arduino for Wildlife Monitoring

FOR FURTHER INFORMATIONS VISIT : https://www.hackster.io/aerodynamics/pibirdhouse-29bddd

## Introduction

Monitoring wildlife in your backyard can provide invaluable data and joyful daily discoveries. This project, **PiBirdHouse**, combines a **Raspberry Pi 4 Model B** with an **Arduino Nano** to create a connected birdhouse featuring:

- Real-time video streaming
- Infrared night vision lighting with PWM control
- Automated shutdown and wake-up for power management
- Bird passage counting with daily and total statistics
- Elegant web interface and data visualisation

It is designed for reliable, standalone field deployment, powered by battery and optionally solar panels.

---

## Wiring Diagram

### Key connections:

- **Camera:** CSI ribbon cable to Pi Camera connector
- **IR LEDs:** Powered from 5V rail, switched via IRF540N (gate to GPIO13 via 330Ω resistor, source to GND, drain to cathode side of LEDs, anodes to 5V via limiting resistors)
- **Arduino Nano:**
  - Analog input for battery voltage divider
  - TX → RX of Raspberry Pi (UART Serial)
  - Wake signal: digital output pin to GPIO3 (Pi wake pin) via logic shifter
- **Raspberry Pi GPIO17:** Connected to Arduino low battery shutdown pin

---

## Software Installation

### Raspberry Pi Setup

First copy all the file from git in a folder @ /home/user_name/PiBirdHouse. Keep the structure of files and folders.

```bash
sudo apt update && sudo apt upgrade
sudo apt install python3-pip python3-venv libcamera-tools
python3 -m venv venv
source venv/bin/activate
pip install flask serial RPi.GPIO opencv-python
```

### Enable camera interface

```bash
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot
```

### Systemd Services

Create:

- `pibirdhouse.service`: Flask server (main web backend)
- `gpio_shutdown.service`: GPIO shutdown monitor (battery protection)
- `bird_detection.service`: bird detection logger (passage counting)

*(See app.py and gpio\_shutdown.py for service integration details).*

---

### Arduino Nano Setup

Upload `ups_raspberry_v1.ino` via Arduino IDE.

#### Functions:

- Reads battery voltage via analog input + voltage divider
- Sends readings via Serial to Raspberry Pi every second
- Generates **wake pulse** on a digital output pin when battery voltage recovers after shutdown

---

## Code Explanation

```bash
PiBirdHouse
│
├── app.py (Flask Backend)
│   ├── / (index.html)
│   ├── /voltage (get battery voltage from Arduino via serial)
│   ├── /status (CPU temp + load avg)
│   ├── /shutdown (system shutdown)
│   ├── /toggle_stream (start/stop stream_server.py)
│   ├── /toggle_ir (LED IR ON/OFF toggle)
│   ├── /set_ir_intensity (set PWM value)
│   └── /api/passages (serve passages.log data for stats.html)
│
├── gpio_shutdown.py (Service)
│   └── Monitors GPIO pin for low battery → triggers safe shutdown
│
├── bird_detection.py (Service)
│   └── Detects bird passages via sensor → logs to static/passages.log
│
├── stream_server.py (Standalone MJPEG Server)
│   ├── Streams live video from picamera2/OpenCV
│   └── Provides capture image function (saved to Images/)
│
├── ups_raspberry_v1.ino (Arduino Nano)
│   ├── Measures LiPo battery voltage via voltage divider
│   ├── Sends voltage data to Raspberry Pi via UART serial
│   └── Sends wake-up pulse when voltage recovers
│
├── templates/
│   ├── index.html
│   │   ├── Logo (logo.png) + Title (PiBirdHouse v1.0)
│   │   ├── Bird passages section (today + total)
│   │   ├── Button to open stats.html
│   │   ├── Video stream control button (start/stop)
│   │   ├── LED IR control button (ON/OFF) + PWM slider
│   │   └── Footer: battery voltage, CPU temp, load avg, project signature
│   │
│   └── stats.html
│       ├── Bargraph: passages per hour (all days aggregated)
│       ├── Bargraph: passages per day (last 365 days)
│       ├── Bargraph: passages per month (monthly summary)
│       └── Return button to index.html
│
├── static/
│   ├── logo.png (favicon + displayed in UI)
│   ├── passages.log (bird passages data file)
│   └── stream_server.py (if launched from static/)
│
├── Images/
│   └── [timestamped_capture_files].jpg
│
└── Services (systemd)
    ├── pibirdhouse.service (runs app.py on boot)
    ├── gpio_shutdown.service (runs gpio_shutdown.py on boot)
    └── bird_detection.service (runs bird_detection.py on boot)
```
### app.py
You have to set your username close to the end of the file in a directory name.
Flask server with routes for:

- `/video_feed`: streaming video frames
- `/start_stream`, `/stop_stream`: control stream\_server.py process
- `/toggle_ir`, `/set_ir_intensity`: control IR LEDs with PWM
- `/voltage`: returns voltage data from Arduino
- `/status`: returns CPU temperature and load average
- `/shutdown`: clean system shutdown
- `/api/passages`: returns JSON bird passages data for stats.html charts

---

### stream\_server.py

Standalone HTTP MJPEG streaming server using **picamera2** or **OpenCV**, accessible at `http://192.168.1.41:8080`.

---

### bird\_detection.py
You have to set your user name on line 9.
Reads IR sensor or GPIO input to detect bird passages, logs entries to `static/passages.log` with:

```
YYYY-MM-DD HH:MM:SS ; daily_total ; overall_total
```

---

### gpio\_shutdown.py

Monitors GPIO17. If it reads **LOW** continuously for a safety period, executes system shutdown to protect battery from over-discharge.

---

## User Interface

### index.html

- **Header:** logo.png (favicon and displayed left) + "PiBirdHouse v1.0" title
- **Bird passages section:** displays today's count and total, with button to open stats.html
- **Video stream control:** toggle button (shows “Start Video” or “Stop Video”)
- **IR LED control:** toggle button (ON/OFF state) + PWM slider for brightness
- **System status footer:** voltage, CPU temperature, load average displayed discreetly

---

### stats.html

Elegant Chart.js bargraphs:

- **By hour:** total bird passages per hour (aggregated over all days)
- **By day:** daily total over last 365 days
- **By month:** monthly summary

Responsive design, modern green (#1b8335) theme for bar colours.

---

## How it Works

1. **Startup:** Pi boots → services launch automatically
2. **Arduino Nano:** sends battery voltage via UART, triggers wake pin if battery is recharged
3. **Flask server:** runs backend routes, renders UI pages
4. **stream\_server.py:** starts/stops on user command to stream video
5. **IR LEDs:** user can turn ON/OFF via PWM slider (auto-off after 1 minute)
6. **Bird detection:** logs entries in passages.log
7. **stats.html:** fetches and visualises passage data via AJAX/Chart.js

---

## Conclusion

With **PiBirdHouse**, you can build an **elegant, autonomous smart birdhouse** for real-time wildlife observation, powered by open-source technologies and robust power management.\
Expand it for species recognition or environmental sensing to create your own DIY nature observatory.


