#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import os
from datetime import datetime

# === Configuration ===
IR_PIN = 18
LOG_FILE = "/home/USER_NAME/PiBirdHouse/static/passages.log"

# === GPIO Initialization ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# === Initialize counters ===
total = 0
daily_total = 0
current_day = datetime.now().date()
raw_count = 0  # raw count of all detections

# === Check if the log file exists and load last totals without incrementing ===
if os.path.isfile(LOG_FILE):
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
        if lines:
            last_line = lines[-1].strip()
            try:
                parts = last_line.split(";")
                if len(parts) >= 3:
                    daily_total = int(parts[1].strip())
                    total = int(parts[2].strip())
            except Exception as e:
                print("Error reading existing log file:", e)

print(f"Resuming with daily_total={daily_total}, total={total}")

print("Waiting for sensor stabilization (1 second)...")
time.sleep(1)  # Pause to avoid false positives at startup

print("IR barrier active (counting half of the passages). Press Ctrl+C to stop.")

try:
    while True:
        if GPIO.input(IR_PIN) == GPIO.HIGH:
            # Passage detected (beam interrupted)
            raw_count += 1

            if raw_count % 2 == 0:
                # Increment only every second detection
                now = datetime.now()
                if now.date() != current_day:
                    # New day: reset daily counter
                    current_day = now.date()
                    daily_total = 1
                else:
                    daily_total += 1

                total += 1

                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                line = f"{timestamp} ; {daily_total} ; {total}\n"

                # Append new record to log file
                with open(LOG_FILE, "a") as f:
                    f.write(line)
                    f.flush()

                print(line.strip())
            else:
                print("Passage detected (not counted)")

            # Debounce: wait until the object leaves the sensor
            while GPIO.input(IR_PIN) == GPIO.HIGH:
                time.sleep(0.05)

        time.sleep(0.05)

except KeyboardInterrupt:
    print("Program stopped by user.")

finally:
    GPIO.cleanup()

