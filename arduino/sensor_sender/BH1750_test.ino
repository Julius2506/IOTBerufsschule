#include <Wire.h>
#include <BH1750.h>

BH1750 lightMeter;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(21, 22);

  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("BH1750 gestartet");
  } else {
    Serial.println("Fehler beim Starten des BH1750");
  }
}

void loop() {
  float lux = lightMeter.readLightLevel();

  Serial.print("Licht: ");
  Serial.print(lux);
  Serial.println(" lx");

  delay(2000);
}