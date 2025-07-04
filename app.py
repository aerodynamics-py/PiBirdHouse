from flask import Flask, render_template, jsonify, request
import serial
import threading
import time
import os
import subprocess
import RPi.GPIO as GPIO

app = Flask(__name__)

# ----- Config GPIO pour LED IR (PWM) -----
LED_PIN = 13
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
pwm = GPIO.PWM(LED_PIN, 1000)
pwm.start(0)
led_on = False

# ----- Variables globales -----
video_process = None
video_running = False

# ----- Port série Arduino -----
try:
    ser = serial.Serial('/dev/serial0', 9600, timeout=1)
    time.sleep(2)
except Exception as e:
    print(f"Erreur ouverture UART : {e}")
    ser = None

voltage_data = {'value': 0.0, 'alert': False}

# ----- Lecture tension en thread -----
def read_voltage():
    while True:
        if ser:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    voltage = float(line)
                    voltage_data['value'] = voltage
                    voltage_data['alert'] = voltage < 3.3
            except Exception as e:
                print(f"Erreur lecture tension : {e}")
        time.sleep(1)

t_thread = threading.Thread(target=read_voltage, daemon=True)
t_thread.start()

# ----- Routes Flask -----

@app.route('/')
def index():
    return render_template('index.html', voltage=voltage_data['value'])

@app.route('/shutdown', methods=['POST'])
def shutdown():
    os.system("sudo /sbin/shutdown -h now")
    return "Raspberry Pi shutting down..."

@app.route('/voltage')
def voltage():
    return jsonify(voltage_data)

@app.route('/status')
def system_status():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            raw_temp = int(f.read())
            temperature = round(raw_temp / 1000.0, 1)
        load_1, load_5, load_15 = os.getloadavg()
        return jsonify({
            'temperature': temperature,
            'load5': round(load_5, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----- LED IR ON/OFF -----
@app.route('/toggle_ir', methods=['POST'])
def toggle_ir():
    global led_on
    if led_on:
        pwm.ChangeDutyCycle(0)
        led_on = False
    else:
        pwm.ChangeDutyCycle(100)
        led_on = True
        threading.Timer(30, auto_turn_off_ir).start()
    return jsonify({'led_on': led_on})

def auto_turn_off_ir():
    global led_on
    pwm.ChangeDutyCycle(0)
    led_on = False

# ----- LED IR Intensity -----
@app.route('/set_ir_intensity', methods=['POST'])
def set_ir_intensity():
    intensity = float(request.form['intensity'])
    pwm.ChangeDutyCycle(intensity)
    return jsonify({'intensity': intensity})

# ----- Stream video start/stop -----
@app.route('/toggle_stream', methods=['POST'])
def toggle_stream():
    global video_process, video_running
    if video_running:
        if video_process:
            video_process.terminate()
            video_process = None
        video_running = False
    else:
        video_process = subprocess.Popen(['/usr/bin/python3', './static/stream_server.py'])
        video_running = True
        threading.Timer(60, auto_stop_stream).start()
    return jsonify({'video_running': video_running})

def auto_stop_stream():
    global video_process, video_running
    if video_process:
        video_process.terminate()
        video_process = None
        video_running = False

# ----- API passages pour stats.html -----
@app.route('/api/passages')
def api_passages():
    data = []
    try:
        with open('./static/passages.log', 'r') as f:
            for line in f:
                parts = line.strip().split(';')
                if len(parts) == 3:
                    data.append({
                        'datetime': parts[0].strip(),
                        'daily': int(parts[1].strip()),
                        'total': int(parts[2].strip())
                    })
    except Exception as e:
        print(f"Erreur lecture passages.log : {e}")
    return jsonify(data)

# ----- Page stats -----
@app.route('/stats')
def stats():
    return render_template('stats.html')
@app.route('/api/passage')
def api_passage():
    try:
        with open('/home/USER_NAME/PiBirdHouse/static/passages.log', 'r') as f:
            data = f.read()
        return data
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
