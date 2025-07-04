import RPi.GPIO as GPIO
import os
import time

# GPIO pin configuration
PIN = 17  # GPIO17 (physical pin 11)

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Monitoring GPIO17 for a sustained LOW signal of 10 seconds...")

try:
    low_start_time = None

    while True:
        pin_state = GPIO.input(PIN)

        if pin_state == GPIO.LOW:
            if low_start_time is None:
                # Start timing when pin goes LOW
                low_start_time = time.time()
            elif time.time() - low_start_time >= 10:
                print("GPIO17 held LOW for 10 seconds. Shutting down system...")
                os.system("sudo halt")
                break
        else:
            low_start_time = None  # Reset if pin goes back HIGH

        time.sleep(0.1)  # Sampling frequency: 10 Hz

except KeyboardInterrupt:
    print("Program interrupted by user.")

finally:
    GPIO.cleanup()

