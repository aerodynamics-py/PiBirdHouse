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

## Bill of Materials (BoM)

| Component                                        | Quantity | Notes                                 |
| ------------------------------------------------ | -------- | ------------------------------------- |
| Raspberry Pi 4 Model B (4GB recommended)         | 1        | Running Raspberry Pi OS Bookworm      |
| Arduino Nano                                     | 1        | For voltage sensing and wake signal   |
| Raspberry Pi Camera Module 3 NoIR Wide           | 1        | IMX708-based for low-light capability |
| PowerBoost 1000C                                 | 1        | For battery boost and charging        |
| LiPo 3.7V Battery                                | 1        | Capacity as needed                    |
| IR LEDs 850nm                                    | 6        | For night illumination                |
| IRF540N or IRLZ44N MOSFET                        | 1        | PWM control of IR LEDs                |
| Logic Level Shifter (BSS138-based)               | 1        | For safe voltage translation          |
| MicroSD Card (16GB+)                             | 1        | Preloaded with RPi OS                 |
| Wires, resistors, soldering tools                | -        | Assembly                              |
| Optional: 3D printed housing or laser-cut panels | -        | Mechanical structure                  |

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


