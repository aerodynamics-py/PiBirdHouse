#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import os
from datetime import datetime

# === Configuration ===
IR_PIN = 18
LOG_FILE = "/home/USER_NAME/PiBirdHouse/static/passages.log"

# === Initialisation GPIO ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# === Initialisation des compteurs ===
total = 0
total_jour = 0
current_day = datetime.now().date()
raw_count = 0  # compteur brut de toutes les détections

# === Vérifier si le fichier existe et récupérer le dernier total sans incrémenter ===
if os.path.isfile(LOG_FILE):
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
        if lines:
            last_line = lines[-1].strip()
            try:
                parts = last_line.split(";")
                if len(parts) >= 3:
                    total_jour = int(parts[1].strip())
                    total = int(parts[2].strip())
            except Exception as e:
                print("Erreur lors de la lecture du fichier existant :", e)

print(f"Reprise avec total_jour={total_jour}, total={total}")

print("Attente de stabilisation du capteur (1 seconde)...")
time.sleep(1)  # Pause pour éviter faux positif à l'initialisation

print("Barrière IR active (détection moitié des passages). Appuyer Ctrl+C pour arrêter.")

try:
    while True:
        if GPIO.input(IR_PIN) == GPIO.HIGH:
            # Passage détecté (faisceau coupé)
            raw_count += 1

            if raw_count % 2 == 0:
                # Incrémenter uniquement une fois sur deux
                now = datetime.now()
                if now.date() != current_day:
                    # Nouveau jour : reset compteur jour
                    current_day = now.date()
                    total_jour = 1
                else:
                    total_jour += 1

                total += 1

                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                line = f"{timestamp} ; {total_jour} ; {total}\n"

                with open(LOG_FILE, "a") as f:
                    f.write(line)
                    f.flush()

                print(line.strip())
            else:
                print("Passage détecté (non compté)")

            # Anti-rebond : attendre que l'objet soit parti
            while GPIO.input(IR_PIN) == GPIO.HIGH:
                time.sleep(0.05)

        time.sleep(0.05)

except KeyboardInterrupt:
    print("Arrêt du programme.")

finally:
    GPIO.cleanup()
