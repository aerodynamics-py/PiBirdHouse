# Import required libraries
from flask import Flask, render_template, jsonify, request  # Flask web framework
import serial                     # To communicate with Arduino via UART
import threading                  # To run tasks in parallel (e.g. voltage reading)
import time                       # For sleep and timing
import os                         # For system commands like shutdown
import subprocess                 # To start/stop external scripts
import RPi.GPIO as GPIO           # To control Raspberry Pi GPIO pins

# Initialize Flask application
app = Flask(__name__)

# ================================
# GPIO Configuration for IR LED
# ================================

# Define the GPIO pin connected to the IR LED (with transistor + PWM)
LED_PIN = 13
GPIO.setmode(GPIO.BCM)            # Use BCM pin numbering
GPIO.setup(LED_PIN, GPIO.OUT)     # Set pin as output

# Create a PWM object on LED_PIN with 1kHz frequency
pwm = GPIO.PWM(LED_PIN, 1000)
pwm.start(0)                      # Start PWM with 0% duty cycle (LED off)
led_on = False                    # State variable to track if LED is on

# ================================
# Global Variables
# ================================
video_process = None              # Process handle for video streaming
video_running = False             # State variable to track if video is running

# ================================
# Initialize Serial Communication with Arduino
# ================================

try:
    # Open serial connection on '/dev/serial0' at 9600 baud rate
    ser = serial.Serial('/dev/serial0', 9600, timeout=1)
    time.sleep(2)  # Wait 2 seconds for Arduino to reset after serial connection
except Exception as e:
    print(f"Error opening UART: {e}")
    ser = None

# Dictionary to store voltage value and alert status
voltage_data = {'value': 0.0, 'alert': False}

# ================================
# Function to continuously read voltage from Arduino in a background thread
# ================================

def read_voltage():
    while True:
        if ser:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    voltage = float(line)                     # Convert read string to float
                    voltage_data['value'] = voltage           # Update voltage value
                    voltage_data['alert'] = voltage < 3.3     # Set alert if voltage < 3.3V
            except Exception as e:
                print(f"Error reading voltage: {e}")
        time.sleep(1)  # Wait 1 second before reading again

# Start the voltage reading thread as a daemon (automatically closes with main program)
t_thread = threading.Thread(target=read_voltage, daemon=True)
t_thread.start()

# ================================
# Flask Routes (Web API Endpoints)
# ================================

@app.route('/')
def index():
    # Render the main HTML page, passing the latest voltage value
    return render_template('index.html', voltage=voltage_data['value'])

@app.route('/shutdown', methods=['POST'])
def shutdown():
    # Shutdown the Raspberry Pi when this route is called via POST
    os.system("sudo /sbin/shutdown -h now")
    return "Raspberry Pi shutting down..."

@app.route('/voltage')
def voltage():
    # Return the current voltage data as JSON (for AJAX requests)
    return jsonify(voltage_data)

@app.route('/status')
def system_status():
    # Return CPU temperature and 5-minute system load as JSON
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            raw_temp = int(f.read())
            temperature = round(raw_temp / 1000.0, 1)  # Convert milli°C to °C
        load_1, load_5, load_15 = os.getloadavg()      # Get system load averages
        return jsonify({
            'temperature': temperature,
            'load5': round(load_5, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================================
# IR LED ON/OFF Toggle Endpoint
# ================================

@app.route('/toggle_ir', methods=['POST'])
def toggle_ir():
    global led_on
    if led_on:
        pwm.ChangeDutyCycle(0)    # Turn off LED by setting duty cycle to 0%
        led_on = False
    else:
        pwm.ChangeDutyCycle(100)  # Turn on LED at full intensity
        led_on = True
        # Start a timer to auto-turn off LED after 30 seconds
        threading.Timer(30, auto_turn_off_ir).start()
    return jsonify({'led_on': led_on})

def auto_turn_off_ir():
    # Function called by timer to auto-turn off IR LED
    global led_on
    pwm.ChangeDutyCycle(0)
    led_on = False

# ================================
# IR LED Intensity Adjustment Endpoint
# ================================

@app.route('/set_ir_intensity', methods=['POST'])
def set_ir_intensity():
    # Receive intensity value from POST request and apply it to PWM
    intensity = float(request.form['intensity'])
    pwm.ChangeDutyCycle(intensity)
    return jsonify({'intensity': intensity})

# ================================
# Video Stream Start/Stop Endpoint
# ================================

@app.route('/toggle_stream', methods=['POST'])
def toggle_stream():
    global video_process, video_running
    if video_running:
        # If video is running, terminate the process to stop it
        if video_process:
            video_process.terminate()
            video_process = None
        video_running = False
    else:
        # If video is not running, start the stream_server.py script
        video_process = subprocess.Popen(['/usr/bin/python3', './static/stream_server.py'])
        video_running = True
        # Auto-stop video after 60 seconds for safety/power saving
        threading.Timer(60, auto_stop_stream).start()
    return jsonify({'video_running': video_running})

def auto_stop_stream():
    # Function to auto-stop video streaming after timer ends
    global video_process, video_running
    if video_process:
        video_process.terminate()
        video_process = None
        video_running = False

# ================================
# API endpoint to get passage data for stats.html
# ================================

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
        print(f"Error reading passages.log: {e}")
    return jsonify(data)

# ================================
# Route to render the stats page
# ================================

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/api/passage')
def api_passage():
    # Return raw passage log data (alternate endpoint)
    try:
        with open('/home/USER_NAME/PiBirdHouse/static/passages.log', 'r') as f:
            data = f.read()
        return data
    except Exception as e:
        return str(e), 500

# ================================
# Run the Flask app on all network interfaces at port 5000
# ================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

