#include <DHT.h>

#define DHTPIN 15
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("Starte DHT11 Test...");
  dht.begin();
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Fehler beim Lesen vom DHT11");
  } else {
    Serial.print("Temperatur: ");
    Serial.print(temperature);
    Serial.print(" °C | Luftfeuchtigkeit: ");
    Serial.print(humidity);
    Serial.println(" %");
  }

  delay(2000);
}