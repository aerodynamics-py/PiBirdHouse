import RPi.GPIO as GPIO
import os
import time

# Configuration de la broche GPIO
PIN = 17  # GPIO17 (broche physique 11)

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Surveillance de GPIO17 pour un signal bas maintenu pendant 5 secondes...")

try:
    low_start_time = None

    while True:
        pin_state = GPIO.input(PIN)

        if pin_state == GPIO.LOW:
            if low_start_time is None:
                low_start_time = time.time()
            elif time.time() - low_start_time >= 10:
                print("GPIO17 maintenu bas pendant 10 secondes. Arrêt du système...")
                os.system("sudo halt")
                break
        else:
            low_start_time = None  # Réinitialiser si le signal repasse à HIGH

        time.sleep(0.1)  # Fréquence d'échantillonnage à 10 Hz

except KeyboardInterrupt:
    print("Interruption par l'utilisateur.")

finally:
    GPIO.cleanup()
