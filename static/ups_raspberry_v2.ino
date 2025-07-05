/**
 * UPS_Raspberry_V1_Nano
 * Mesure la tension batterie via pont diviseur sur A0 avec référence interne 1.1V.
 * Si la tension < seuil bas (3.25V), l'Arduino entre en mode sleep (surveillance).
 * Si la tension >= seuil haut (3.7V), l'Arduino envoie une impulsion de wake au Raspberry Pi.
 *
 * Carte : Arduino Nano (ATmega328P)
 * Auteur : Adaptation professionnelle ChatGPT
 */

#include <avr/sleep.h>
#include <avr/wdt.h>

// Broches et constantes
const int pinLecture = A0; // Pin analogique de lecture de tension
const int pinWake = 3;     // Pin digitale pour wake Raspberry Pi

const float seuilBas = 3.3; // Seuil bas (V) - sous lequel on entre en surveillance
const float seuilHaut = 3.8; // Seuil haut (V) - au-dessus duquel on envoie un wake

const float Vref = 1.08;      // Référence interne ADC (V)

// Pont diviseur R1=10k / R2=2.2 => ratio ~0.1793 (adapter si besoin)
const float dividerRatio = 0.1793;

void setup() {
  Serial.begin(9600);
  analogReference(INTERNAL); // Utilise la référence interne 1.1V
  delay(5); // Stabilisation recommandée

  pinMode(pinWake, OUTPUT);
  digitalWrite(pinWake, LOW); // Initialise wake pin à LOW

}

void loop() {
  float tension = mesureTension(); // Mesure tension batterie
  //Serial.print("Battery Voltage: ");
  Serial.println(tension);
  //Serial.println(" V");

  if (tension >= seuilHaut) {
    // Si tension >= seuil haut, envoie impulsion de wake au Raspberry Pi
    //Serial.println("Voltage above upper threshold. Sending wake pulse.");
    wakeRaspberryPi();
  }

  delay(1000); // Petite pause avant prochaine mesure
}

/**
 * Fonction : mesureTension
 * Lit la pin analogique et calcule la tension réelle en fonction du pont diviseur.
 */
float mesureTension() {
  int val = analogRead(pinLecture);
  float voltage = (val * Vref) / 1023.0; // Convertit ADC en tension à A0
  voltage = voltage / dividerRatio; // Calcule tension réelle batterie
  return voltage;
}

/**
 * Fonction : wakeRaspberryPi
 * Envoie une impulsion de 100ms sur pinWake pour réveiller le Raspberry Pi.
 */
void wakeRaspberryPi() {
  digitalWrite(pinWake, HIGH);
  delay(100); // Durée de l'impulsion : 100ms
  digitalWrite(pinWake, LOW);
}
