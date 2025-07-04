const int pinVs = A0;          // Broche analogique pour Vs
const int pinSortie = 3;       // Broche de sortie digitale

const float seuilwakeVs = 3.7;
const float seuilbasVs = 3.25;
const unsigned long intervalleMesure = 1000; // 1 minute en ms

const unsigned long delaiExtinction = 5000; // 5 secondes

bool mesureActive = false;
bool wakeup_pulse = false;

unsigned long dernierTempsMesure = 0;
unsigned long tempsSousSeuil = 0;
bool enSousSeuil = false;

void setup() {
  pinMode(pinSortie, OUTPUT);
  digitalWrite(pinSortie, LOW);
  Serial.begin(9600);
}

void loop() {
  mesureActive = true;

  if (mesureActive && millis() - dernierTempsMesure >= intervalleMesure) {
    dernierTempsMesure = millis();

    int valeurBrute = analogRead(pinVs);
    float vcc = readVcc() / 1000.0; // En volts
    float tensionVs = valeurBrute * (vcc / 1023.0);
    Serial.println(tensionVs);

    if (tensionVs < seuilbasVs) {
      // On est sous le seuil bas
      if (!enSousSeuil) {
        // Passage sous le seuil => début du chrono
        enSousSeuil = true;
        tempsSousSeuil = millis();
      } else {
        // On est déjà sous le seuil, vérifier délai
        if (!wakeup_pulse && (millis() - tempsSousSeuil >= delaiExtinction)) {
          // Délai dépassé, on déclenche le pulse
          wakeup_pulse = true;
        }
      }
    } else {
      // Tension au-dessus du seuil bas => reset
      enSousSeuil = false;
      wakeup_pulse = false;
    }

    // Gérer l’envoi du pulse si conditions remplies
    if (tensionVs > seuilwakeVs && wakeup_pulse) {
      digitalWrite(pinSortie, HIGH);
      delay(100);
      digitalWrite(pinSortie, LOW);
      wakeup_pulse = false;
    }
  }
}

long readVcc() {
  // Mesure la référence interne 1.1V via l'ADC, ce qui permet d'en déduire Vcc
  ADMUX = _BV(REFS0) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1);
  delay(2); // Attente pour stabiliser
  ADCSRA |= _BV(ADSC); // Lancer la conversion
  while (bit_is_set(ADCSRA, ADSC)); // Attendre la fin
  uint16_t result = ADC;
  long vcc = 1098238L / result; // 1.084*1023*1000
  return vcc; // en millivolts
}
